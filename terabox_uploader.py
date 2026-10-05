#!/usr/bin/env python3
"""
TeraBox Universal Auto-Uploader & Auto-Deleter
==============================================
Multi-OS + Multi-Browser + FULL SUBFOLDER SUPPORT
- Creates remote folder structure
- Uploads nested files one-by-one into matching paths
- Deletes local files after confirmed upload

Repository: https://github.com/vincevision/terabox-auto-uploader
License: MIT
"""

import os
import sys
import time
import platform
import argparse
from pathlib import Path
from urllib.parse import quote

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager


class SystemDetector:
    @staticmethod
    def get_os() -> str:
        if "TERMUX_VERSION" in os.environ or "/data/data/com.termux" in os.getenv("PREFIX", ""):
            return "termux"
        system = platform.system().lower()
        if "darwin" in system:
            return "mac"
        if "windows" in system:
            return "windows"
        return "linux"

    @classmethod
    def locate_browser(cls, browser_type: str) -> tuple:
        current_os = cls.get_os()
        browser_type = browser_type.lower()

        paths = {
            "linux": {
                "brave": ["/usr/bin/brave-browser", "/usr/bin/brave", "/snap/bin/brave"],
                "chrome": ["/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"],
                "firefox": ["/usr/bin/firefox"],
                "edge": ["/usr/bin/microsoft-edge"],
            },
            "windows": {
                "brave": [
                    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                    r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
                ],
                "chrome": [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                ],
                "firefox": [
                    r"C:\Program Files\Mozilla Firefox\firefox.exe",
                    r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
                ],
                "edge": [
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                ],
            },
            "mac": {
                "brave": ["/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"],
                "chrome": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
                "firefox": ["/Applications/Firefox.app/Contents/MacOS/firefox"],
                "edge": ["/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"],
            },
            "termux": {
                "chrome": ["/data/data/com.termux/files/usr/bin/chromium"],
                "firefox": ["/data/data/com.termux/files/usr/bin/firefox"],
            },
        }

        os_map = paths.get(current_os, paths["linux"])

        if browser_type == "auto":
            for b_name in ["brave", "chrome", "firefox", "edge"]:
                for p in os_map.get(b_name, []):
                    if os.path.exists(p):
                        return b_name, p
            return "chrome", None

        for p in os_map.get(browser_type, []):
            if os.path.exists(p):
                return browser_type, p

        return browser_type, None


class UniversalUploader:
    def __init__(
        self,
        local_folder: str,
        cookie_input: str,
        remote_root: str = "/uploads",
        browser_type: str = "auto",
        watch: bool = False,
        headless: bool = True,
        preserve_structure: bool = True,
    ):
        self.local_folder = os.path.abspath(os.path.expanduser(local_folder))
        self.remote_root = remote_root.rstrip("/") or "/uploads"
        self.watch = watch
        self.headless = headless
        self.preserve_structure = preserve_structure
        self.ndus = self._extract_ndus(cookie_input)
        self.os_type = SystemDetector.get_os()
        self.browser_name, self.binary_path = SystemDetector.locate_browser(browser_type)
        self.created_remote_dirs = set()

        if not os.path.isdir(self.local_folder):
            print(f"[*] Folder '{self.local_folder}' does not exist. Creating it now...")
            os.makedirs(self.local_folder, exist_ok=True)

        print(f"\n[*] Detected OS      : {self.os_type.upper()}")
        print(f"[*] Selected Engine  : {self.browser_name.upper()}")
        print(f"[*] Local Folder     : {self.local_folder}")
        print(f"[*] Remote Root      : {self.remote_root}")
        print(f"[*] Preserve Structure: {self.preserve_structure}")
        if self.binary_path:
            print(f"[+] Binary Path      : {self.binary_path}")

        self.driver = self._init_driver()

    @staticmethod
    def _extract_ndus(cookie_input: str) -> str:
        cookie_input = cookie_input.strip().strip("'").strip('"')
        if "ndus=" in cookie_input:
            for part in cookie_input.split(";"):
                if "ndus=" in part:
                    return part.split("=", 1)[1].strip()
        return cookie_input

    def _init_driver(self):
        print("[*] Launching browser engine driver...")

        if self.browser_name == "firefox":
            from selenium.webdriver.firefox.options import Options as FirefoxOptions

            options = FirefoxOptions()
            if self.headless:
                options.add_argument("--headless")
            if self.binary_path:
                options.binary_location = self.binary_path
            service = FirefoxService(GeckoDriverManager().install())
            return webdriver.Firefox(service=service, options=options)

        if self.browser_name == "edge":
            from selenium.webdriver.edge.options import Options as EdgeOptions

            options = EdgeOptions()
            if self.headless:
                options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            if self.binary_path:
                options.binary_location = self.binary_path
            service = EdgeService(EdgeChromiumDriverManager().install())
            return webdriver.Edge(service=service, options=options)

        from selenium.webdriver.chrome.options import Options as ChromeOptions

        options = ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1366,768")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        if self.binary_path:
            options.binary_location = self.binary_path

        try:
            service = ChromeService(ChromeDriverManager().install())
        except Exception:
            service = ChromeService()

        return webdriver.Chrome(service=service, options=options)

    def login(self) -> bool:
        print("[*] Connecting to TeraBox...")
        try:
            self.driver.get("https://www.terabox.com/main")
            time.sleep(2)
            self.driver.add_cookie(
                {
                    "name": "ndus",
                    "value": self.ndus,
                    "domain": ".terabox.com",
                    "path": "/",
                    "secure": True,
                }
            )
            self.driver.refresh()
            time.sleep(6)

            if "login" in self.driver.current_url.lower():
                print("[-] Login failed. Cookie is invalid or expired.")
                return False

            print("[+] SUCCESS: Authenticated successfully!")
            # Ensure remote root exists
            self.ensure_remote_dir(self.remote_root)
            return True
        except Exception as e:
            print(f"[-] Login exception: {e}")
            return False

    def _path_to_url(self, remote_path: str) -> str:
        # TeraBox expects URL-encoded path like %2Fuploads%2Fphotos
        encoded = quote(remote_path if remote_path.startswith("/") else f"/{remote_path}", safe="")
        return f"https://www.terabox.com/main?category=all&path={encoded}"

    def navigate_to_remote(self, remote_path: str):
        url = self._path_to_url(remote_path)
        self.driver.get(url)
        time.sleep(4)

    def ensure_remote_dir(self, remote_path: str) -> bool:
        """Create remote directory path step-by-step if missing."""
        remote_path = remote_path.replace("\\", "/").rstrip("/")
        if not remote_path.startswith("/"):
            remote_path = "/" + remote_path

        if remote_path in self.created_remote_dirs or remote_path in ("", "/"):
            return True

        parts = [p for p in remote_path.split("/") if p]
        current = ""

        for part in parts:
            parent = current if current else "/"
            current = f"{current}/{part}" if current else f"/{part}"

            if current in self.created_remote_dirs:
                continue

            print(f"[*] Ensuring remote folder: {current}")
            self.navigate_to_remote(parent)
            time.sleep(2)

            # If already exists, navigating directly often works; try create anyway
            try:
                # Click New Folder button (multiple possible selectors)
                created = False
                selectors = [
                    "//button[contains(., 'New Folder')]",
                    "//div[contains(@class,'create') and contains(., 'New Folder')]",
                    "//span[contains(., 'New Folder')]/ancestor::button",
                    "//button[contains(@class,'create')]",
                ]

                for sel in selectors:
                    buttons = self.driver.find_elements(By.XPATH, sel)
                    if buttons:
                        buttons[0].click()
                        time.sleep(1)
                        created = True
                        break

                if not created:
                    # Fallback: open path directly; if missing TeraBox may still allow upload path later
                    self.navigate_to_remote(current)
                    self.created_remote_dirs.add(current)
                    continue

                # Type folder name into input
                inputs = self.driver.find_elements(By.XPATH, "//input[@type='text']")
                if not inputs:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, "input")

                if inputs:
                    box = inputs[-1]
                    box.clear()
                    box.send_keys(part)
                    time.sleep(0.5)
                    box.send_keys(Keys.ENTER)
                    time.sleep(2)
                    print(f"[+] Created/ready: {current}")
                else:
                    print(f"[!] Could not find folder name input for: {part}")

                self.created_remote_dirs.add(current)
            except Exception as e:
                print(f"[!] Folder create warning for {current}: {e}")
                self.created_remote_dirs.add(current)

        return True

    def is_transfer_complete(self) -> bool:
        try:
            html = self.driver.page_source
            if (
                "Upload Complete" in html
                or "Transfer Complete" in html
                or "Uploaded successfully" in html
                or "upload completed" in html.lower()
            ):
                return True
            close_btns = self.driver.find_elements(By.CLASS_NAME, "u-panel-close")
            if len(close_btns) > 0 and "100%" in html:
                return True
            return False
        except Exception:
            return False

    def collect_files(self):
        """Collect files recursively with relative paths."""
        items = []
        for root, dirs, files in os.walk(self.local_folder):
            # skip hidden dirs
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for name in sorted(files):
                if name.startswith("."):
                    continue
                if name.endswith((".tmp", ".crdownload", ".part", ".partial")):
                    continue
                full = os.path.join(root, name)
                rel = os.path.relpath(full, self.local_folder)
                items.append((full, rel))
        items.sort(key=lambda x: x[1])
        return items

    def remote_dir_for(self, rel_path: str) -> str:
        rel_path = rel_path.replace("\\", "/")
        parent = os.path.dirname(rel_path).replace("\\", "/")
        if not self.preserve_structure or parent in ("", "."):
            return self.remote_root
        return f"{self.remote_root}/{parent}"

    def upload_file(self, file_path: str, rel_path: str) -> bool:
        file_name = os.path.basename(file_path)
        size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
        remote_dir = self.remote_dir_for(rel_path)

        print(f"\n[*] Uploading: {rel_path} ({size_mb} MB)")
        print(f"[*] Remote dir: {remote_dir}")

        try:
            # Ensure destination folder exists, then navigate there
            self.ensure_remote_dir(remote_dir)
            self.navigate_to_remote(remote_dir)
            time.sleep(3)

            file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
            if not file_inputs:
                print("[-] File upload element not found on page.")
                return False

            file_inputs[0].send_keys(file_path)
            print("[*] Monitoring upload status...")

            timeout = 1800  # 30 minutes for large nested batches
            start = time.time()
            while time.time() - start < timeout:
                if self.is_transfer_complete():
                    print(f"[+] Server confirmed upload: {rel_path}")
                    time.sleep(4)
                    return True
                time.sleep(4)

            print(f"[-] Upload timed out: {rel_path}")
            return False
        except Exception as e:
            print(f"[-] Transfer error ({rel_path}): {e}")
            return False

    def cleanup_empty_dirs(self):
        """Remove empty local subfolders after uploads."""
        for root, dirs, files in os.walk(self.local_folder, topdown=False):
            if root == self.local_folder:
                continue
            try:
                if not os.listdir(root):
                    os.rmdir(root)
                    print(f"[+] Removed empty local folder: {root}")
            except OSError:
                pass

    def run(self):
        if not self.login():
            self.driver.quit()
            sys.exit(1)

        print(f"\n[+] WATCHING FOLDER: {self.local_folder}")
        print(f"[*] Mode: {'Continuous Watch' if self.watch else 'One-time Sync'}")
        print("[*] Nested folders will be recreated on TeraBox\n")

        try:
            while True:
                files = self.collect_files()

                if not files:
                    if not self.watch:
                        print("[*] Folder empty. Sync finished.")
                        break
                    time.sleep(5)
                    continue

                print(f"[*] Queued {len(files)} file(s) (including nested files)")

                for full_path, rel_path in files:
                    if not os.path.exists(full_path):
                        continue

                    if self.upload_file(full_path, rel_path):
                        try:
                            os.remove(full_path)
                            print(f"[+] DELETED LOCAL FILE: {rel_path}")
                        except OSError as e:
                            print(f"[-] Could not delete local file: {e}")
                    time.sleep(2)

                # After batch, clean empty dirs
                self.cleanup_empty_dirs()

                if not self.watch:
                    break

                time.sleep(5)

        except KeyboardInterrupt:
            print("\n[*] Stopping uploader safely...")
        finally:
            self.driver.quit()


def interactive_wizard():
    print(
        """
  ╔════════════════════════════════════════════════════╗
  ║       TERABOX AUTO-UPLOADER SETUP WIZARD           ║
  ║           (with nested folder support)             ║
  ╚════════════════════════════════════════════════════╝
    """
    )

    default_folder = os.path.expanduser("~/terabox_sync")
    folder = input(f"[?] Enter local folder path to watch [{default_folder}]: ").strip()
    if not folder:
        folder = default_folder

    remote = input("[?] Remote root folder on TeraBox [/uploads]: ").strip()
    if not remote:
        remote = "/uploads"
    if not remote.startswith("/"):
        remote = "/" + remote

    cookie = input("\n[?] Paste your TeraBox 'ndus' cookie value (or full cookie string): ").strip()
    while not cookie:
        print("[-] Cookie is required!")
        cookie = input("[?] Paste your TeraBox 'ndus' cookie value: ").strip()

    print("\n[?] Select Browser Engine:")
    print("    1) Auto-Detect (Recommended)")
    print("    2) Brave")
    print("    3) Google Chrome")
    print("    4) Mozilla Firefox")
    print("    5) Microsoft Edge")
    browser_choice = input("    Select (1-5) [default 1]: ").strip()
    browser_map = {"1": "auto", "2": "brave", "3": "chrome", "4": "firefox", "5": "edge"}
    browser = browser_map.get(browser_choice, "auto")

    watch_ans = input("\n[?] Enable Continuous Watch Mode? (y/n) [default: y]: ").strip().lower()
    watch = False if watch_ans == "n" else True

    show_ans = input("[?] Show Browser Window on screen? (y/n) [default: n]: ").strip().lower()
    show_browser = True if show_ans == "y" else False

    return {
        "folder": folder,
        "remote": remote,
        "cookie": cookie,
        "browser": browser,
        "watch": watch,
        "show_browser": show_browser,
    }


def main():
    parser = argparse.ArgumentParser(description="TeraBox Universal Auto-Uploader (Nested Folders Supported)")
    parser.add_argument("-f", "--folder", help="Local directory to monitor")
    parser.add_argument("-r", "--remote", default="/uploads", help="Remote root folder on TeraBox (default: /uploads)")
    parser.add_argument("-c", "--cookie", help="TeraBox cookie containing ndus=")
    parser.add_argument(
        "-b",
        "--browser",
        default="auto",
        choices=["auto", "chrome", "brave", "firefox", "edge"],
        help="Browser engine to use (default: auto)",
    )
    parser.add_argument("-w", "--watch", action="store_true", help="Monitor folder continuously")
    parser.add_argument("--show-browser", action="store_true", help="Show browser GUI (default: hidden)")
    parser.add_argument(
        "--flat",
        action="store_true",
        help="Do NOT preserve subfolders (upload all files into remote root only)",
    )

    args = parser.parse_args()

    if not args.folder or not args.cookie:
        data = interactive_wizard()
        folder = data["folder"]
        remote = data["remote"]
        cookie = data["cookie"]
        browser = data["browser"]
        watch = data["watch"]
        headless = not data["show_browser"]
        preserve = True
    else:
        folder = args.folder
        remote = args.remote
        cookie = args.cookie
        browser = args.browser
        watch = args.watch
        headless = not args.show_browser
        preserve = not args.flat

    uploader = UniversalUploader(
        local_folder=folder,
        cookie_input=cookie,
        remote_root=remote,
        browser_type=browser,
        watch=watch,
        headless=headless,
        preserve_structure=preserve,
    )
    uploader.run()


if __name__ == "__main__":
    main()
