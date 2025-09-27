# `handlers/song_handler.py` Walkthrough

This document explains each stage of the `/song` command handler and its helpers.

## Module setup
- Imports `asyncio`, `logging`, `shutil`, `tempfile`, and `pathlib.Path` for asynchronous execution, diagnostics, and filesystem management.
- Pulls in aiogram primitives (`Router`, `types`, `Command`, `CommandObject`, `FSInputFile`) to register the handler and send Telegram audio attachments.
- Imports `yt_dlp` so the bot can search YouTube and extract audio streams.
- Configures a module-level logger and router instances that aiogram will include during startup.

## `_download_audio`
1. Receives the user-supplied query along with a temporary directory path created by the handler.
2. Builds `yt_dlp` options that:
   - Download only the best audio stream (`bestaudio/best`).
   - Store files inside the provided temp directory.
   - Suppress playlist downloads and noisy output.
   - Run the `FFmpegExtractAudio` post-processor to convert the result to a 192 kbps MP3 file.
3. Uses `yt_dlp.YoutubeDL` to execute a `ytsearch1:` query for the first relevant video and download its audio track.
4. Validates that the search produced at least one entry and locates the file generated in the temp directory.
5. Returns the absolute path to the audio file along with the video title for later use in the Telegram response.

## `song_command`
1. Triggered when a user sends `/song` with optional search terms. Aiogram passes a `CommandObject` so the handler can extract the query text.
2. If the user omits arguments, it replies with usage guidance and exits early.
3. Posts a "Searching" status message to keep the chat responsive while the download runs.
4. Creates a unique temporary directory (`tempfile.mkdtemp`) and prepares to track the downloaded file path for cleanup.
5. Offloads `_download_audio` to a background thread via `loop.run_in_executor` so the synchronous `yt_dlp` work doesn’t block the asyncio event loop.
6. Once the download finishes, edits the status message to reflect that the audio is being sent, wraps the file with `FSInputFile`, and delivers it via `answer_audio`, including a caption referencing YouTube as the source.
7. On success, removes the status message to keep the chat tidy.
8. On any exception, logs the stack trace and informs the user that the download failed.
9. In all cases, deletes the temporary audio file (if it exists) and removes the temporary directory using `shutil.rmtree` so the bot doesn’t leak files.

