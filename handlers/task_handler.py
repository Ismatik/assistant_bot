from __future__ import annotations

import logging
from typing import List

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils import task_storage

logger = logging.getLogger(__name__)
router = Router()


class TaskStates(StatesGroup):
    waiting_for_task_text = State()


def _format_tasks(tasks: List[dict]) -> str:
    if not tasks:
        return (
            "You don't have any saved tasks yet.\n"
            "Use the button below or send /addtask <task> to record one."
        )

    lines = ["🗒️ <b>Your tasks:</b>"]
    for idx, task in enumerate(tasks, start=1):
        lines.append(f"{idx}. {task['text']}")
    lines.append("\nTap a button to add a task or mark one as done.")
    return "\n".join(lines)


def _build_keyboard(tasks: List[dict]) -> InlineKeyboardMarkup:
    buttons: List[List[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="➕ Add task", callback_data="task_add")]
    ]

    for idx, task in enumerate(tasks, start=1):
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"✅ Done {idx}",
                    callback_data=f"task_done:{task['id']}",
                )
            ]
        )

    if tasks:
        buttons.append(
            [InlineKeyboardButton(text="🧹 Clear all", callback_data="task_clear")]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _send_task_overview(message: types.Message, tasks: List[dict]) -> None:
    await message.answer(
        _format_tasks(tasks),
        reply_markup=_build_keyboard(tasks),
        parse_mode="HTML",
    )


@router.message(Command("tasks"))
async def tasks_command(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    tasks = task_storage.list_tasks(message.from_user.id)
    await _send_task_overview(message, tasks)


@router.message(Command("addtask"))
async def add_task_command(message: types.Message) -> None:
    task_text = message.get_args().strip()
    if not task_text:
        await message.answer(
            "Please provide a task description.\nExample: <code>/addtask Review project proposal</code>",
            parse_mode="HTML",
        )
        return

    task = task_storage.add_task(message.from_user.id, task_text)
    logger.info("Added task %s for user %s", task["id"], message.from_user.id)
    tasks = task_storage.list_tasks(message.from_user.id)
    await message.answer("✅ Task saved.")
    await _send_task_overview(message, tasks)


@router.callback_query(F.data == "task_add")
async def task_add_button(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer()
    await state.set_state(TaskStates.waiting_for_task_text)
    await callback_query.message.answer(
        "Please send me the task description.\nSend /cancel to stop adding a task.",
    )


@router.message(TaskStates.waiting_for_task_text)
async def capture_task_text(message: types.Message, state: FSMContext) -> None:
    task_text = message.text.strip()
    if not task_text:
        await message.answer("Task text cannot be empty. Please try again or send /cancel.")
        return

    task = task_storage.add_task(message.from_user.id, task_text)
    logger.info("Added task %s for user %s", task["id"], message.from_user.id)
    await state.clear()
    tasks = task_storage.list_tasks(message.from_user.id)
    await message.answer("✅ Task saved.")
    await _send_task_overview(message, tasks)


@router.message(Command("cancel"), TaskStates.waiting_for_task_text)
async def cancel_task_add(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Task creation cancelled.")


@router.callback_query(F.data.startswith("task_done:"))
async def task_done_callback(callback_query: types.CallbackQuery) -> None:
    await callback_query.answer()
    _, task_id_str = callback_query.data.split(":", 1)
    try:
        task_id = int(task_id_str)
    except ValueError:
        logger.warning("Received invalid task id '%s'", task_id_str)
        return

    removed = task_storage.remove_task(callback_query.from_user.id, task_id)
    tasks = task_storage.list_tasks(callback_query.from_user.id)
    text = _format_tasks(tasks)
    reply_markup = _build_keyboard(tasks)

    if removed:
        await callback_query.message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    else:
        await callback_query.answer("Task not found.", show_alert=True)


@router.callback_query(F.data == "task_clear")
async def task_clear_callback(callback_query: types.CallbackQuery) -> None:
    await callback_query.answer()
    task_storage.clear_tasks(callback_query.from_user.id)
    tasks = task_storage.list_tasks(callback_query.from_user.id)
    await callback_query.message.edit_text(
        _format_tasks(tasks),
        reply_markup=_build_keyboard(tasks),
        parse_mode="HTML",
    )
