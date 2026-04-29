"""Completion checks for Arctic Shift downloads."""

from __future__ import annotations

import time

from selenium.webdriver.remote.webdriver import WebDriver


def wait_for_download_complete(
    driver: WebDriver,
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> None:
    """Wait until Arctic Shift reports that writing is complete."""

    started_at = time.monotonic()

    while time.monotonic() - started_at < timeout_seconds:
        if _download_finished(driver):
            return

        time.sleep(poll_interval_seconds)

    raise TimeoutError(f"Arctic Shift did not finish after {timeout_seconds} seconds")


def _download_finished(driver: WebDriver) -> bool:
    script = """
    function visible(node) {
      if (!node) return false;
      const style = window.getComputedStyle(node);
      const box = node.getBoundingClientRect();
      return style.visibility !== 'hidden'
        && style.display !== 'none'
        && box.width > 0
        && box.height > 0;
    }

    const hasNewDownload = [...document.querySelectorAll('button')].some((button) => {
      const text = (button.innerText || button.textContent || '').trim().toLowerCase();
      return text.includes('new download') && visible(button);
    });
    const bodyText = (document.body.innerText || '').toLowerCase();
    return hasNewDownload || bodyText.includes('download complete');
    """
    try:
        return bool(driver.execute_script(script))
    except Exception:
        return False
