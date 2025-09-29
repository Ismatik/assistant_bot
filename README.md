# Ismat Assistant Bot

A Telegram AI assistant built for Ismat that combines Google Gemini-powered multi-turn chat, direct YouTube audio downloads via `/song`, and a lightweight personal task manager accessible through inline buttons. The bot is designed to run on top of [aiogram](https://docs.aiogram.dev/en/latest/) and integrates external tools like `ffmpeg` and `yt-dlp` to provide a rich multimedia experience.

## Features
- **Conversational AI chat** – Gemini models handle multi-turn conversations with automatic Markdown-to-HTML formatting in Telegram.
- **YouTube audio extraction** – `/song` retrieves audio using `yt-dlp` and `ffmpeg`, then sends the track directly in chat.
- **Inline task manager** – `/tasks` opens an interactive list with buttons to complete or remove entries, while `/addtask` and `/clear` help manage personal to-dos.
- **Model selection shortcuts** – Users can switch between Gemini models through inline buttons or the `/select_model` command.
- **Activity logging** – User interactions and system events are appended to `files/user_activity.log` for later review.

## Prerequisites
- Python 3.11 or newer.
- Telegram Bot API token.
- Google Gemini API key.
- External executables: [`ffmpeg`](https://ffmpeg.org/) and [`yt-dlp`](https://github.com/yt-dlp/yt-dlp). The bot checks for both during startup and logs a warning if they are missing.

## Installation
1. **Clone the repository and install dependencies**
   ```bash
   git clone https://github.com/<your-username>/assistant_bot.git
   cd assistant_bot
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Configure secrets**
   Create a `.env` file in the project root with the required tokens:
   ```env
   BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   GEMINI_API_KEY=your-gemini-key
   ```

## Running the Bot
After installing dependencies and configuring the environment variables, start the bot with:
```bash
python ismat_assistant_bot.py
```

The script sets up logging to both STDOUT and `files/user_activity.log` (see `config_reader.py`). Ensure the `files/` directory exists and is writable before running in production.

## Commands
| Command | Description |
| --- | --- |
| `/start` | Sends a welcome message and displays available features. |
| `/help` | Lists supported commands and usage tips. |
| `/song <query or YouTube URL>` | Downloads audio through `yt-dlp`/`ffmpeg` and sends the resulting file. |
| `/tasks` | Opens the inline to-do manager showing current items and action buttons. |
| `/addtask <text>` | Adds a new entry to the task list. |
| `/clear` | Clears the current list of tasks. |
| `/select_model` | Presents Gemini model options for the chat experience. |

## Logging and Data Storage
- **Log location:** `files/user_activity.log` (configured in `config_reader.py`).
- **Retention:** Logs grow over time; rotate or archive them periodically if deploying long term.
- **Privacy:** Review compliance requirements before logging sensitive user data.

## Suggested Repository "About" Text
> Telegram AI assistant for Ismat with Google Gemini chat, YouTube audio downloads via /song, and inline to-do management.

