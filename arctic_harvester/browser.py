from __future__ import annotations

from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

from arctic_harvester.config import HarvesterConfig


def build_driver(config: HarvesterConfig) -> webdriver.Chrome | webdriver.Edge:
    config.download_dir.mkdir(parents=True, exist_ok=True)
    if config.browser == "chrome":
        options = _chrome_options(config.download_dir, config.headless)
        return webdriver.Chrome(options=options)
    if config.browser == "edge":
        options = _edge_options(config.download_dir, config.headless)
        return webdriver.Edge(options=options)
    raise ValueError(f"Unsupported browser {config.browser}")


def _download_preferences(download_dir: Path) -> dict[str, object]:
    return {
        "download.default_directory": str(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }


def _chrome_options(download_dir: Path, headless: bool) -> ChromeOptions:
    options = ChromeOptions()
    options.add_experimental_option("prefs", _download_preferences(download_dir))
    options.add_argument("--disable-notifications")
    if headless:
        options.add_argument("--headless=new")
    return options


def _edge_options(download_dir: Path, headless: bool) -> EdgeOptions:
    options = EdgeOptions()
    options.add_experimental_option("prefs", _download_preferences(download_dir))
    options.add_argument("--disable-notifications")
    if headless:
        options.add_argument("--headless=new")
    return options
