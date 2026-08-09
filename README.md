# SEB Protector

A Windows desktop tool that uses a Gemini Vision+Text model to analyze screenshots and user prompts.

## Overview

`XENBOT.py` is a Python application that provides:
- a GUI front-end built with `customtkinter`
- a screenshot selection tool using `PyQt5`
- image enhancement using `Pillow`
- text and image prompt handling for Google Gemini via `google.generativeai`
- API key rotation to recover from failed requests

The app can either send a prompt-only request or capture a screenshot and ask Gemini to troubleshoot the image.

## Features

- Select a screen region interactively
- Enhance captured screenshots automatically
- Send prompts + screenshots to Gemini Vision model
- Rotate between multiple API keys on failure
- Clear response history
- Switch active API key from the UI

## Requirements

- Python 3.10+ (recommended)
- `PyQt5`
- `Pillow`
- `pyautogui`
- `customtkinter`
- `google-generativeai`

## Installation

1. Clone or copy the repository to your local machine.
2. Create and activate a Python virtual environment.
3. Install dependencies:

```powershell
python -m pip install PyQt5 Pillow pyautogui customtkinter google-generativeai
```

## Configuration

Open `XENBOT.py` and update the `GEMINI_API_KEYS` list with valid Gemini API keys.

```python
GEMINI_API_KEYS = [
    "YOUR_API_KEY_1",
    "YOUR_API_KEY_2",
    ...
]
```

Optionally, update `MODEL_NAME` if you want to use a different Gemini model.

## Usage

Run the script:

```powershell
python XENBOT.py
```

Controls:
- `Enter prompt here` — type a text prompt
- `Send Prompt` — send only text to Gemini
- `Troubleshoot` — capture the screen region and send the screenshot with prompt
- `Clear` — clear the response history
- API buttons — switch between configured Gemini API keys

## Notes

- The app uses a transparent full-screen overlay for region selection.
- Captured screenshots are enhanced for contrast and sharpness before upload.
- If a request fails, the script attempts up to 3 retries with key rotation.
- The UI is intentionally small and lightweight.

## Security

- Do not commit actual API keys to source control.
- Keep valid keys in a secure local configuration or environment variables for production use.

## License

This repository does not include a license file. Add one if you plan to share it publicly.
