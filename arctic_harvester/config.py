from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class HarvesterConfig:
    browser: str
    subreddits_file: Path
    users_file: Path
    download_tool_url: str
    start_date: str
    end_date: str
    download_posts: bool
    download_comments: bool
    download_dir: Path
    wait_after_download_seconds: float
    download_timeout_seconds: float
    poll_interval_seconds: float
    headless: bool


def _string_value(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def load_config(config_path: Path) -> HarvesterConfig:
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    base_dir = config_path.parent
    browser = _string_value(raw.get("browser", "chrome")).lower()
    if browser not in {"chrome", "edge"}:
        raise ValueError('browser must be "chrome" or "edge"')

    start_date = _string_value(raw.get("start_date", ""))
    end_date = _string_value(raw.get("end_date", "")) or date.today().isoformat()

    return HarvesterConfig(
        browser=browser,
        subreddits_file=(base_dir / _string_value(raw.get("subreddits_file", "inputs/subreddits.txt"))).resolve(),
        users_file=(base_dir / _string_value(raw.get("users_file", "inputs/users.txt"))).resolve(),
        download_tool_url=_string_value(raw.get("download_tool_url", "https://arctic-shift.photon-reddit.com/download-tool")),
        start_date=start_date,
        end_date=end_date,
        download_posts=bool(raw.get("download_posts", True)),
        download_comments=bool(raw.get("download_comments", True)),
        download_dir=(base_dir / _string_value(raw.get("download_dir", "downloads"))).resolve(),
        wait_after_download_seconds=float(raw.get("wait_after_download_seconds", 5)),
        download_timeout_seconds=float(raw.get("download_timeout_seconds", 1800)),
        poll_interval_seconds=float(raw.get("poll_interval_seconds", 2)),
        headless=bool(raw.get("headless", False)),
    )
