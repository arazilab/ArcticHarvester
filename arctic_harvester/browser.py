"""Browser setup for the Selenium scraper."""

from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

from arctic_harvester.config import HarvesterConfig


def build_driver(config: HarvesterConfig) -> webdriver.Chrome | webdriver.Edge:
    """Create a visible Chrome or Edge driver."""

    if config.browser == "chrome":
        return webdriver.Chrome(options=_chrome_options())
    if config.browser == "edge":
        return webdriver.Edge(options=_edge_options())
    raise ValueError(f"Unsupported browser {config.browser}")


def _chrome_options() -> ChromeOptions:
    options = ChromeOptions()
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    return options


def _edge_options() -> EdgeOptions:
    options = EdgeOptions()
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    return options
