from __future__ import annotations

from pathlib import Path
import time

from selenium.webdriver.remote.webdriver import WebDriver

TEMP_SUFFIXES = {".crdownload", ".part", ".tmp", ".download"}


def wait_for_download(
    driver: WebDriver,
    download_dir: Path,
    known_files: set[Path],
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> list[Path]:
    started_at = time.monotonic()
    last_seen: list[Path] = []
    stable_since: float | None = None

    while time.monotonic() - started_at < timeout_seconds:
        current_files = set(download_dir.glob("*"))
        new_files = sorted(current_files - known_files)
        temp_files = [path for path in new_files if path.suffix.lower() in TEMP_SUFFIXES]
        completed = [path for path in new_files if path.is_file() and path.suffix.lower() not in TEMP_SUFFIXES]

        if completed and not temp_files:
            if completed == last_seen:
                if stable_since is not None and time.monotonic() - stable_since >= max(1.0, poll_interval_seconds):
                    return completed
            else:
                last_seen = completed
                stable_since = time.monotonic()

        if _page_looks_finished(driver) and completed:
            return completed

        time.sleep(poll_interval_seconds)

    raise TimeoutError(f"No completed download appeared in {download_dir} after {timeout_seconds} seconds")


def _page_looks_finished(driver: WebDriver) -> bool:
    script = """
    const progress = [...document.querySelectorAll('progress,[role="progressbar"]')];
    if (!progress.length) return false;
    return progress.every((item) => {
      const max = Number(item.getAttribute('max') || item.getAttribute('aria-valuemax') || 100);
      const value = Number(item.value || item.getAttribute('aria-valuenow') || 0);
      return max > 0 && value >= max;
    });
    """
    try:
        return bool(driver.execute_script(script))
    except Exception:
        return False
