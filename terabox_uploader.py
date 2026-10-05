#!/usr/bin/env python3
"""
TeraBox Universal Auto-Uploader & Auto-Deleter
==============================================
Multi-OS (Linux, Windows, macOS, Termux) & Multi-Browser (Chrome, Brave, Firefox, Edge)
Supports both Interactive Wizard mode and CLI arguments mode.

Repository: https://github.com/vincevision/terabox-auto-uploader
License: MIT
"""

import os
import sys
import time
import platform
import argparse
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager


class SystemDetector:
    """Detects Operating System environment and browser binary locations."""

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
        """Returns (browser_type, binary_path)."""
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
                    r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"
                ],
                "chrome": [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                ],
                "firefox": [
                    r"C:\Program Files\Mozilla Firefox\firefox.exe",
                    r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
                ],
                "edge": [
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
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
            }
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
    """Multi-OS & Multi-Browser driver orchestrator."""

    def __init__(self, local_folder: str, cookie_input: str, browser_type: str = "auto",
                 watch: bool = False, headless: bool = True):
        self.local_folder = os.path.abspath(os.path.expanduser(local_folder))
        self.watch = watch
        self.headless = headless
        self.ndus = self._extract_ndus(cookie_input)
        self.os_type = SystemDetector.get_os()
        self.browser_name, self.binary_path = SystemDetector.locate_browser(browser_type)

        if not os.path.isdir(self.local_folder):
            print(f"[*] Folder '{self.local_folder}' does not exist. Creating it now...")
            os.makedirs(self.local_folder, exist_ok=True)

        print(f"\n[*] Detected OS     : {self.os_type.upper()}")
        print(f"[*] Selected Engine : {self.browser_name.upper()}")
        if self.binary_path:
            print(f"[+] Binary Path     : {self.binary_path}")

        self.driver = self._init_driver()

    @staticmethod
    def _extract_ndus(cookie_input: str) -> str:
        cookie_input = cookie_input.strip().strip("'").strip('"')
        if "ndus=" in cookie_input:
            for part in cookie_input.split(";"):
                if "ndus=" in part:
                    return part.split("=")[1].strip()
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

        elif self.browser_name == "edge":
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

        else:
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
            self.driver.add_cookie({
                "name": "ndus",
                "value": self.ndus,
                "domain": ".terabox.com",
                "path": "/",
                "secure": True
            })
            self.driver.refresh()
            time.sleep(6)

            if "login" in self.driver.current_url.lower():
                print("[-] Login failed. Cookie is invalid or expired.")
                return False

            print("[+] SUCCESS: Authenticated successfully!")
            return True
        except Exception as e:
            print(f"[-] Login exception: {e}")
            return False

    def is_transfer_complete(self) -> bool:
        try:
            html = self.driver.page_source
            if "Upload Complete" in html or "Transfer Complete" in html or "Uploaded successfully" in html:
                return True
            close_btns = self.driver.find_elements(By.CLASS_NAME, "u-panel-close")
            if len(close_btns) > 0 and "100%" in html:
                return True
            return False
        except Exception:
            return False

    def upload_file(self, file_path: str) -> bool:
        file_name = os.path.basename(file_path)
        size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
        print(f"\n[*] Uploading: {file_name} ({size_mb} MB)")

        try:
            self.driver.get("https://www.terabox.com/main")
            time.sleep(4)

            file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
            if not file_inputs:
                print("[-] File upload element not found on page.")
                return False

            file_inputs[0].send_keys(file_path)
            print("[*] Monitoring status...")

            timeout = 1200  # 20 minutes limit
            start_time = time.time()

            while time.time() - start_time < timeout:
                if self.is_transfer_complete():
                    print(f"[+] Server confirmed upload: {file_name}")
                    time.sleep(5)
                    return True
                time.sleep(4)

            print(f"[-] Upload timed out: {file_name}")
            return False

        except Exception as e:
            print(f"[-] Transfer error ({file_name}): {e}")
            return False

    def run(self):
        if not self.login():
            self.driver.quit()
            sys.exit(1)

        print(f"\n[+] WATCHING FOLDER: {self.local_folder}")
        print(f"[*] Mode: {'Continuous Watch' if self.watch else 'One-time Sync'}\n")

        try:
            while True:
                files = [
                    os.path.join(self.local_folder, f)
                    for f in os.listdir(self.local_folder)
                    if os.path.isfile(os.path.join(self.local_folder, f)) and not f.startswith(".")
                ]

                if not files:
                    if not self.watch:
                        print("[*] Folder empty. Sync finished.")
                        break
                    time.sleep(5)
                    continue

                files.sort()

                for file_path in files:
                    file_name = os.path.basename(file_path)
                    if file_name.endswith((".tmp", ".crdownload", ".part")):
                        continue

                    if self.upload_file(file_path):
                        try:
                            os.remove(file_path)
                            print(f"[+] DELETED LOCAL FILE: {file_name}")
                        except OSError as e:
                            print(f"[-] Could not delete local file: {e}")

                    time.sleep(3)

                if not self.watch:
                    break

        except KeyboardInterrupt:
            print("\n[*] Stopping uploader safely...")
        finally:
            self.driver.quit()


def interactive_wizard():
    """Interactive CLI setup when no command-line arguments are provided."""
    print("""
  ╔════════════════════════════════════════════════════╗
  ║       TERABOX AUTO-UPLOADER SETUP WIZARD           ║
  ╚════════════════════════════════════════════════════╝
    """)

    default_folder = os.path.expanduser("~/terabox_sync")
    folder = input(f"[?] Enter local folder path to watch [{default_folder}]: ").strip()
    if not folder:
        folder = default_folder

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
        "cookie": cookie,
        "browser": browser,
        "watch": watch,
        "show_browser": show_browser,
    }


def main():
    parser = argparse.ArgumentParser(description="TeraBox Universal Auto-Uploader")
    parser.add_argument("-f", "--folder", help="Local directory to monitor")
    parser.add_argument("-c", "--cookie", help="TeraBox cookie containing ndus=")
    parser.add_argument("-b", "--browser", default="auto", choices=["auto", "chrome", "brave", "firefox", "edge"],
                        help="Browser engine to use (default: auto)")
    parser.add_argument("-w", "--watch", action="store_true", help="Monitor folder continuously")
    parser.add_argument("--show-browser", action="store_true", help="Show browser GUI (default: hidden)")

    args = parser.parse_args()

    if not args.folder or not args.cookie:
        wizard_data = interactive_wizard()
        folder = wizard_data["folder"]
        cookie = wizard_data["cookie"]
        browser = wizard_data["browser"]
        watch = wizard_data["watch"]
        headless = not wizard_data["show_browser"]
    else:
        folder = args.folder
        cookie = args.cookie
        browser = args.browser
        watch = args.watch
        headless = not args.show_browser

    uploader = UniversalUploader(
        local_folder=folder,
        cookie_input=cookie,
        browser_type=browser,
        watch=watch,
        headless=headless
    )
    uploader.run()


if __name__ == "__main__":
    main()