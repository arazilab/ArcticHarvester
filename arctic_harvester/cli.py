"""Command line entry point for ArcticHarvester."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import time

from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm

from arctic_harvester.browser import build_driver
from arctic_harvester.config import HarvesterConfig, load_config
from arctic_harvester.downloads import wait_for_download_complete
from arctic_harvester.page import click_start, fill_download_form


@dataclass(frozen=True)
class HarvestItem:
    """One subreddit or user request from the input files."""

    kind: str
    name: str

    @property
    def form_value(self) -> str:
        return f"{self.clean_kind}/{self.clean_name}"

    @property
    def clean_name(self) -> str:
        clean = self.name.strip()
        if clean.startswith(("r/", "u/")):
            return clean[2:]
        return clean

    @property
    def clean_kind(self) -> str:
        clean = self.name.strip()
        if clean.startswith("r/"):
            return "r"
        if clean.startswith("u/"):
            return "u"
        return self.kind


@dataclass
class BrowserTabs:
    """Track open tabs so old pages can stay alive for recent downloads."""

    driver: WebDriver
    handles: list[str]
    max_open_tabs: int

    @classmethod
    def from_current_tab(cls, driver: WebDriver, max_open_tabs: int) -> BrowserTabs:
        return cls(
            driver=driver,
            handles=[driver.current_window_handle],
            max_open_tabs=max_open_tabs,
        )

    def open_fresh_page(self, url: str, step_delay_seconds: float) -> None:
        self.driver.switch_to.new_window("tab")
        new_handle = self.driver.current_window_handle
        self.handles.append(new_handle)
        self.driver.get(url)
        self._close_old_tabs()
        self.driver.switch_to.window(new_handle)
        _pause(step_delay_seconds)

    def _close_old_tabs(self) -> None:
        while len(self.handles) > self.max_open_tabs:
            old_handle = self.handles.pop(0)
            self.driver.switch_to.window(old_handle)
            self.driver.close()


def main() -> None:
    """Run the command line scraper."""

    args = _parse_args()
    config = load_config(args.config)
    items = _load_items(config)

    if not items:
        print("No subreddits or users found. Check the input files.")
        return

    _validate_config(config)
    _run_selenium(config, items)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch download Reddit data through Arctic Shift.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.toml"),
        help="Path to the TOML config file.",
    )
    return parser.parse_args()


def _load_items(config: HarvesterConfig) -> list[HarvestItem]:
    """Read subreddit and user input files."""

    items: list[HarvestItem] = []
    items.extend(HarvestItem("r", name) for name in _read_lines(config.subreddits_file))
    items.extend(HarvestItem("u", name) for name in _read_lines(config.users_file))
    return items


def _read_lines(path: Path) -> list[str]:
    """Read non-empty lines, skipping comments."""

    if not path.exists():
        return []
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        clean = line.strip()
        if clean and not clean.startswith("#"):
            lines.append(clean)
    return lines


def _validate_config(config: HarvesterConfig) -> None:
    if not config.download_posts and not config.download_comments:
        raise ValueError("At least one of download_posts or download_comments must be true")
    if config.wait_after_download_seconds < 0:
        raise ValueError("wait_after_download_seconds must be zero or greater")
    if config.poll_interval_seconds <= 0:
        raise ValueError("poll_interval_seconds must be greater than zero")
    if config.max_open_tabs < 1:
        raise ValueError("max_open_tabs must be one or greater")


def _run_selenium(config: HarvesterConfig, items: list[HarvestItem]) -> None:
    """Process all items in a visible browser."""

    driver = build_driver(config)
    try:
        driver.get(config.download_tool_url)
        _pause(config.step_delay_seconds)
        tabs = BrowserTabs.from_current_tab(driver, config.max_open_tabs)
        with tqdm(total=len(items), unit="item") as pbar:
            for index, item in enumerate(items):
                pbar.set_description(f"Downloading {item.form_value}")

                fill_download_form(
                    driver=driver,
                    item_kind=item.clean_kind,
                    item_name=item.clean_name,
                    start_date=config.start_date,
                    end_date=config.end_date,
                    download_posts=config.download_posts,
                    download_comments=config.download_comments,
                    step_delay_seconds=config.step_delay_seconds,
                )
                _pause(config.step_delay_seconds)
                click_start(driver)

                wait_for_download_complete(
                    driver=driver,
                    timeout_seconds=config.download_timeout_seconds,
                    poll_interval_seconds=config.poll_interval_seconds,
                )
                pbar.write(f"Arctic Shift finished {item.form_value}")
                pbar.update(1)
                pbar.refresh()

                if index < len(items) - 1:
                    tabs.open_fresh_page(config.download_tool_url, config.step_delay_seconds)
                if config.wait_after_download_seconds:
                    time.sleep(config.wait_after_download_seconds)
    finally:
        driver.quit()


def _pause(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)


if __name__ == "__main__":
    main()
