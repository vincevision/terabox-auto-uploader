# TeraBox Auto-Uploader

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A small Python utility that watches a local folder, uploads each new file to TeraBox, and deletes the local copy after the upload is confirmed by the browser session.

This project uses Selenium and browser automation to sign in with your TeraBox session cookie and interact with the website as a real browser session.

## Features

- Interactive setup wizard for first-time use
- Watches a local directory for new files
- Uploads files one at a time
- Deletes local files only after upload success is detected
- Supports Chrome, Brave, Firefox, and Edge
- Works on Linux, Windows, macOS, and Termux
- Can run headless by default or show the browser window with a flag

## How it works

- The script reads a local folder path and monitors it for files.
- It logs in to TeraBox using a session cookie named `ndus`.
- It uploads files by sending them through the website upload input.
- When the browser reports completion, it removes the local file.
- If `--watch` is enabled, the script continues monitoring the folder.

## Requirements

- Python 3.8+
- A browser installed on the system
- A valid TeraBox `ndus` cookie

Install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Getting your `ndus` cookie

1. Log in to TeraBox in your browser.
2. Open Developer Tools with `F12`.
3. Go to the Cookies section for `https://www.terabox.com`.
4. Copy the value of the `ndus` cookie.

> Keep this cookie private. It is effectively your session credential.

## Usage

### Interactive mode (recommended)

Run the script without arguments:

```bash
python terabox_uploader.py
```

The wizard will ask for:

- local folder path
- TeraBox cookie value
- browser engine
- whether to watch continuously
- whether to show the browser window

### Command-line mode

```bash
python terabox_uploader.py -f ~/terabox_sync -c "ndus=YOUR_COOKIE" --watch
```

Use a specific browser:

```bash
python terabox_uploader.py -f ~/terabox_sync -c "ndus=YOUR_COOKIE" --browser brave --watch
```

Show the browser window instead of running headless:

```bash
python terabox_uploader.py -f ~/terabox_sync -c "ndus=YOUR_COOKIE" --watch --show-browser
```

## CLI options

| Option | Long form | Description |
|---|---|---|
| `-f` | `--folder` | Local directory to monitor |
| `-c` | `--cookie` | TeraBox cookie string or `ndus` value |
| `-b` | `--browser` | Browser engine: `auto`, `chrome`, `brave`, `firefox`, `edge` |
| `-w` | `--watch` | Keep monitoring the folder continuously |
|  | `--show-browser` | Display the browser window instead of using headless mode |

## Example workflow

```bash
git clone https://github.com/vincevision/terabox-auto-uploader.git
cd terabox-auto-uploader
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python terabox_uploader.py
```

Then enter:

- your sync folder, such as `~/terabox_sync`
- your `ndus` cookie value
- browser choice
- watch mode preference

## Notes

- The tool deletes local files only after the upload is judged complete by the website.
- Temporary files like `.tmp`, `.part`, and `.crdownload` are skipped.
- This project is designed for browser automation and may require browser-specific setup depending on your OS.
- It is intended for personal use and should comply with TeraBox terms of service and local laws.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

