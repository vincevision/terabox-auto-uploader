# TeraBox Auto-Uploader (by VICENT)

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Python utility that uploads files from a local folder to TeraBox using Selenium and a browser session. It can process a folder once or continue watching it, and it attempts to recreate subfolders on TeraBox.

> **Important: uploaded files are deleted locally.** The script deletes each local file when it detects an upload-complete message on the website, and removes empty local subfolders. This detection depends on the TeraBox interface and is not a separate verification of the remote file. Keep backups and test with copies before using important data.

## Requirements

- [Git](https://git-scm.com/downloads) to clone the repository.
- [Python 3.8 or newer](https://www.python.org/downloads/) and pip. On Windows, select **Add Python to PATH** when installing Python.
- An installed browser: Chrome/Chromium, Brave, Firefox, or Microsoft Edge.
- A TeraBox account and a valid `ndus` session cookie.
- Internet access for installing dependencies, downloading browser drivers, and uploading files. Browser and driver compatibility may require additional setup on your system.

## Step-by-step installation

Open a terminal (or PowerShell on Windows). Run the commands for your operating system below.

### 1. Clone the repository

```bash
git clone https://github.com/vincevision/terabox-auto-uploader.git
cd terabox-auto-uploader
```

All remaining commands should be run from this `terabox-auto-uploader` directory.

### 2. Create and activate a virtual environment

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows PowerShell:**

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, consult Microsoft's guidance on [PowerShell execution policies](https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_execution_policies), or use Command Prompt instead:

```bat
venv\Scripts\activate.bat
```

If `venv` creation fails on Linux, install your distribution's Python virtual environment package (often `python3-venv`) and try again.

### 3. Install Python dependencies

With the virtual environment activated, run:

```bash
python -m pip install -r requirements.txt
```

This installs Selenium and webdriver-manager. The script uses webdriver-manager to obtain browser drivers; make sure your browser and its driver are compatible.

### 4. Get your TeraBox cookie

1. Sign in to [TeraBox](https://www.terabox.com/) in your browser.
2. Open Developer Tools (usually `F12`).
3. Open the browser's storage/cookies panel: **Application → Cookies** in Chromium-based browsers, or **Storage → Cookies** in Firefox.
4. Select the TeraBox site and copy the value of the cookie named `ndus`.

Treat this cookie like a password: anyone with it may be able to access your session. Do not share it, commit it to Git, or paste it into screenshots. If it expires, sign in again and obtain a fresh value.

### 5. Start the setup wizard

With the virtual environment activated, run:

```bash
python terabox_uploader.py
```

The wizard asks for:

1. **Local folder:** the folder to upload from (default `~/terabox_sync`; created if it does not exist). Use a dedicated folder containing copies for your first test.
2. **Remote root:** the destination folder in TeraBox (default `/uploads`).
3. **Cookie:** paste your `ndus` value or a full cookie string containing `ndus=...`.
4. **Browser:** choose auto-detect or select an installed browser.
5. **Continuous watch:** choose whether to keep monitoring for new files (default yes). Choose `n` for a one-time run.
6. **Show browser:** choose whether to display the browser window (default no, meaning headless).

The script processes existing eligible files as well as new files in watch mode. Press **Ctrl+C** to stop watching. Check the destination in TeraBox after your test.

### 6. Run it again later

Open a terminal in the cloned repository, activate the virtual environment using the command from step 2, and run `python terabox_uploader.py` again. To leave the virtual environment when finished, run `deactivate`.

## Command-line usage

To bypass the wizard, provide both a local folder and a cookie. For example, on Linux/macOS:

```bash
python terabox_uploader.py -f ~/terabox_sync -c "ndus=YOUR_COOKIE" --watch
```

For Windows PowerShell, a local folder can be supplied as a quoted path:

```powershell
python terabox_uploader.py -f "$HOME\terabox_sync" -c "ndus=YOUR_COOKIE" --watch
```

Replace `YOUR_COOKIE` with your actual cookie value. **Command-line cookies may be visible in shell history or process listings**; use the interactive wizard if you want to avoid placing the cookie in a command. Terminal input may still be visible on screen.

For example, to choose a destination and browser and show the browser window:

```bash
python terabox_uploader.py -f ~/terabox_sync -c "ndus=YOUR_COOKIE" -r /backups -b brave --watch --show-browser
```

Without `--watch`, command-line mode performs a one-time run. Use `python terabox_uploader.py --help` to see all options.

| Option | Description |
|---|---|
| `-f`, `--folder` | Local directory to process |
| `-c`, `--cookie` | `ndus` value or cookie string containing it |
| `-r`, `--remote` | Remote root folder (default `/uploads`) |
| `-b`, `--browser` | `auto`, `chrome`, `brave`, `firefox`, or `edge` (default `auto`) |
| `-w`, `--watch` | Keep monitoring the folder after processing existing files |
| `--show-browser` | Show the browser instead of running headless |
| `--flat` | Upload all files to the remote root instead of preserving subfolders (command-line mode only) |

If either `--folder` or `--cookie` is missing, the script opens the wizard instead of using the supplied command-line settings.

## Notes and troubleshooting

- Files are processed recursively, one at a time. Hidden files and directories and files ending in `.tmp`, `.part`, `.partial`, or `.crdownload` are skipped.
- If the browser cannot start, check that it is installed and compatible with the downloaded driver; try choosing it explicitly with `--browser` or run with `--show-browser` to investigate.
- If login fails, obtain a fresh `ndus` cookie. Website changes can also break the browser automation or its upload-completion detection.
- The script includes Termux detection, but browser and WebDriver availability may require extra setup; the desktop installation steps do not guarantee Termux compatibility.
- Use this tool in accordance with TeraBox's terms of service and applicable laws.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
