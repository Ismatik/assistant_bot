import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Tuple

from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import FSInputFile

import yt_dlp


logger = logging.getLogger(__name__)
router = Router()


def _download_audio(search_query: str, temp_dir: str) -> Tuple[str, str]:
    """Download the best audio track for the first YouTube search result."""

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(Path(temp_dir) / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(f"ytsearch1:{search_query}", download=True)

        if not search_results:
            raise ValueError("No search results returned from YouTube.")

        if "entries" in search_results:
            video_info = search_results["entries"][0]
        else:
            video_info = search_results

        downloaded_files = sorted(Path(temp_dir).glob("*"))
        if not downloaded_files:
            raise FileNotFoundError("Audio file was not created by yt-dlp.")

        audio_path = str(downloaded_files[-1])
        title = video_info.get("title", "Unknown Title")

        return audio_path, title


@router.message(Command("song"))
async def song_command(message: types.Message, command: CommandObject | None = None) -> None:
    """Handle the /song command and send an audio file back to the user."""

    query = command.args.strip() if command and command.args else ""

    if not query:
        await message.answer("Please provide a song title or keywords, e.g. /song Never Gonna Give You Up")
        return

    status_message = await message.answer("🔎 Searching for your song...")
    temp_dir = tempfile.mkdtemp(prefix="song_dl_")
    audio_file_path: str | None = None

    try:
        loop = asyncio.get_running_loop()
        audio_file_path, title = await loop.run_in_executor(None, _download_audio, query, temp_dir)

        await status_message.edit_text("⬇️ Downloading and sending the track...")

        audio_input = FSInputFile(audio_file_path)
        await message.answer_audio(
            audio=audio_input,
            caption=f"{title}\nSource: YouTube",
            title=title,
        )

        await status_message.delete()
    except Exception:  # noqa: BLE001 - provide feedback to the user
        logger.exception("Failed to process /song command")
        await status_message.edit_text(
            "⚠️ Sorry, I couldn't download that track. Please try again later or choose another song."
        )
    finally:
        if audio_file_path:
            try:
                Path(audio_file_path).unlink(missing_ok=True)
            except Exception:
                logger.debug("Failed to remove audio file %s", audio_file_path, exc_info=True)

        shutil.rmtree(temp_dir, ignore_errors=True)

