"""Selenium helpers for the Arctic Shift page."""

from __future__ import annotations

import time

from selenium.common.exceptions import JavascriptException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def fill_download_form(
    driver: WebDriver,
    item_kind: str,
    item_name: str,
    start_date: str,
    end_date: str,
    download_posts: bool,
    download_comments: bool,
    step_delay_seconds: float,
) -> None:
    """Fill one Arctic Shift form for a subreddit or user."""

    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    _select_kind(driver, item_kind)
    _pause(step_delay_seconds)

    name_input = _find_name_input(driver, item_kind)
    _replace_value(driver, name_input, item_name)
    _blur(driver, name_input)
    _pause(step_delay_seconds)

    if start_date:
        _replace_value(driver, _find_control(driver, ["start date"]), start_date)
        _pause(step_delay_seconds)
    if end_date:
        _replace_value(driver, _find_control(driver, ["end date"]), end_date)
        _pause(step_delay_seconds)

    _set_checkbox(driver, "download-posts", download_posts)
    _pause(step_delay_seconds)
    _set_checkbox(driver, "download-comments", download_comments)
    _pause(step_delay_seconds)


def click_start(driver: WebDriver) -> None:
    """Click Start after Arctic Shift enables it."""

    button = _find_enabled_button(driver, "start", timeout_seconds=60)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
    button.click()


def _replace_value(driver: WebDriver, element: WebElement, value: str) -> None:
    """Set an input value and notify Svelte listeners."""

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    element.click()
    element.clear()
    element.send_keys(value)
    driver.execute_script("""
    arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
    arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
    """, element)


def _blur(driver: WebDriver, element: WebElement) -> None:
    driver.execute_script("arguments[0].blur(); document.body.click();", element)


def _pause(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)


def _select_kind(driver: WebDriver, item_kind: str) -> None:
    text = "r/" if item_kind == "r" else "u/"
    button = _find_button(driver, text)
    selected = "selected" in (button.get_attribute("class") or "")
    if not selected:
        button.click()


def _find_name_input(driver: WebDriver, item_kind: str) -> WebElement:
    placeholder = "Subreddit name" if item_kind == "r" else "User name"
    return WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f'input[placeholder="{placeholder}"]'))
    )


def _set_checkbox(driver: WebDriver, checkbox_id: str, desired: bool) -> None:
    """Match a checkbox to the configured true or false value."""

    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, checkbox_id)))
    checked = _checkbox_checked(driver, element)
    if checked != desired:
        clicked = bool(
            driver.execute_script(
                """
                const checkbox = arguments[0];

                function visible(node) {
                  if (!node) return false;
                  const style = window.getComputedStyle(node);
                  const box = node.getBoundingClientRect();
                  return style.visibility !== 'hidden'
                    && style.display !== 'none'
                    && box.width > 0
                    && box.height > 0;
                }

                const candidates = [
                  checkbox.closest('label'),
                  checkbox.id ? document.querySelector(`label[for="${CSS.escape(checkbox.id)}"]`) : null,
                  checkbox.parentElement,
                  checkbox.parentElement ? checkbox.parentElement.parentElement : null,
                  checkbox,
                ];

                const target = candidates.find(visible);
                if (!target) return false;
                target.scrollIntoView({block: 'center'});
                target.click();
                return true;
                """,
                element,
            )
        )
        if not clicked:
            raise RuntimeError(f"Could not click checkbox {checkbox_id}")

    checked = _checkbox_checked(driver, element)
    if checked != desired:
        raise RuntimeError(f"Could not set checkbox {checkbox_id}")


def _checkbox_checked(driver: WebDriver, element: WebElement) -> bool:
    return bool(
        driver.execute_script(
            """
            const checkbox = arguments[0];
            return checkbox.checked || checkbox.getAttribute('aria-checked') === 'true';
            """,
            element,
        )
    )


def _find_control(driver: WebDriver, label_candidates: list[str], input_type: str | None = None) -> WebElement:
    """Find an input by nearby label text."""

    script = """
    const labels = arguments[0].map((value) => value.toLowerCase());
    const inputType = arguments[1];
    const controls = [...document.querySelectorAll('input, textarea, select')];

    function textFor(control) {
      const direct = control.id ? document.querySelector(`label[for="${CSS.escape(control.id)}"]`) : null;
      const wrapped = control.closest('label');
      const parent = control.parentElement;
      const grand = parent ? parent.parentElement : null;
      return [direct, wrapped, parent, grand]
        .filter(Boolean)
        .map((node) => node.innerText || node.textContent || '')
        .join(' ')
        .toLowerCase();
    }

    for (const control of controls) {
      if (inputType && (control.type || '').toLowerCase() !== inputType) continue;
      const text = textFor(control);
      const placeholder = (control.placeholder || '').toLowerCase();
      const aria = (control.getAttribute('aria-label') || '').toLowerCase();
      if (labels.some((label) => text.includes(label) || placeholder.includes(label) || aria.includes(label))) {
        return control;
      }
    }
    return null;
    """
    try:
        element = driver.execute_script(script, label_candidates, input_type)
    except JavascriptException:
        element = None

    if element is not None:
        return element

    fallback = "input"
    if input_type:
        fallback = f'input[type="{input_type}"]'
    try:
        return WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, fallback)))
    except TimeoutException as exc:
        labels = ", ".join(label_candidates)
        raise RuntimeError(f"Could not find form control for {labels}") from exc


def _find_button(driver: WebDriver, text: str) -> WebElement:
    script = """
    const wanted = arguments[0].toLowerCase();
    const buttons = [...document.querySelectorAll('button,input[type="button"],input[type="submit"]')];
    return buttons.find((button) => {
      const text = (button.innerText || button.value || '').trim().toLowerCase();
      return text === wanted || text.includes(wanted);
    }) || null;
    """
    element = driver.execute_script(script, text)
    if element is not None:
        return element
    xpath = f"//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"
    return WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))


def _find_enabled_button(driver: WebDriver, text: str, timeout_seconds: float) -> WebElement:
    """Wait for a visible button to become enabled."""

    script = """
    const wanted = arguments[0].toLowerCase();
    const buttons = [...document.querySelectorAll('button,input[type="button"],input[type="submit"]')];
    return buttons.find((button) => {
      const text = (button.innerText || button.value || '').trim().toLowerCase();
      return (text === wanted || text.includes(wanted)) && !button.disabled;
    }) || null;
    """

    def find_enabled(_: WebDriver) -> WebElement | bool:
        element = driver.execute_script(script, text)
        return element if element is not None else False

    return WebDriverWait(driver, timeout_seconds).until(find_enabled)
