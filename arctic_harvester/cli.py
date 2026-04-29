from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import time

from tqdm import tqdm

from arctic_harvester.browser import build_driver
from arctic_harvester.config import HarvesterConfig, load_config
from arctic_harvester.downloads import wait_for_download
from arctic_harvester.page import click_start, fill_download_form


@dataclass(frozen=True)
class HarvestItem:
    kind: str
    name: str

    @property
    def form_value(self) -> str:
        clean = self.name.strip()
        if clean.startswith(("r/", "u/")):
            return clean
        return f"{self.kind}/{clean}"


def main() -> None:
    args = _parse_args()
    config = load_config(args.config)
    items = _load_items(config)

    if not items:
        print("No subreddits or users found. Check the input files.")
        return

    _validate_config(config)
    _run(config, items)


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
    items: list[HarvestItem] = []
    items.extend(HarvestItem("r", name) for name in _read_lines(config.subreddits_file))
    items.extend(HarvestItem("u", name) for name in _read_lines(config.users_file))
    return items


def _read_lines(path: Path) -> list[str]:
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


def _run(config: HarvesterConfig, items: list[HarvestItem]) -> None:
    driver = build_driver(config)
    try:
        driver.get(config.download_tool_url)
        with tqdm(total=len(items), unit="item") as pbar:
            for item in items:
                pbar.set_description(f"Downloading {item.form_value}")
                known_files = set(config.download_dir.glob("*"))

                fill_download_form(
                    driver=driver,
                    item_value=item.form_value,
                    start_date=config.start_date,
                    end_date=config.end_date,
                    download_posts=config.download_posts,
                    download_comments=config.download_comments,
                )
                click_start(driver)

                new_files = wait_for_download(
                    driver=driver,
                    download_dir=config.download_dir,
                    known_files=known_files,
                    timeout_seconds=config.download_timeout_seconds,
                    poll_interval_seconds=config.poll_interval_seconds,
                )
                pbar.write(f"Downloaded {item.form_value} -> {', '.join(path.name for path in new_files)}")

                if config.wait_after_download_seconds:
                    time.sleep(config.wait_after_download_seconds)
                driver.refresh()
                pbar.update(1)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
