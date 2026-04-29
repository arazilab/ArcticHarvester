![ArcticHarvester banner](assets/banner.png)

# ArcticHarvester

ArcticHarvester batch downloads Reddit data through the Arctic Shift download tool.

It uses Selenium to open Chrome or Edge, fill the form, and start each download. Arctic Shift writes files through the browser save picker, so you must approve each save dialog.

After Arctic Shift shows `New download` or `Download complete`, ArcticHarvester updates the progress bar, waits for the configured delay, opens a fresh Arctic Shift tab, closes the old tab, and starts the next item.

## What It Does

- Reads subreddit names from `inputs/subreddits.txt`
- Reads usernames from `inputs/users.txt`
- Skips empty input files
- Accepts names like `AskReddit`, `r/AskReddit`, `spez`, or `u/spez`
- Uses `r/` mode for subreddit entries and `u/` mode for user entries
- Sets start and end dates only when you provide them
- Leaves blank dates alone so Arctic Shift can use its defaults
- Downloads posts, comments, or both
- Uses `tqdm` to show item progress

## Important Limit

Arctic Shift uses `window.showSaveFilePicker()`. This is a browser security feature. Selenium cannot fully bypass it on macOS.

This means the workflow is semi-automatic. You can let the browser work, but you need to approve the save picker for each output file. If both posts and comments are enabled, expect two save dialogs for each subreddit or user.

## Requirements

- Python 3.11 or newer
- Google Chrome or Microsoft Edge
- Internet access

The browser must stay visible. Headless mode is not supported by this app.

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -qqq -e .
```

## Set Up

Copy the example config.

```bash
cp config.example.toml config.toml
```

Edit `config.toml`.

```toml
browser = "chrome"
start_date = ""
end_date = ""
download_posts = true
download_comments = true
wait_after_download_seconds = 5
step_delay_seconds = 2
download_timeout_seconds = 1800
poll_interval_seconds = 2
```

Use `browser = "edge"` for Microsoft Edge.

Dates must use `YYYY-MM-DD`.

Blank `start_date` keeps the earliest date Arctic Shift loads after the name is entered.

Blank `end_date` keeps Arctic Shift's default `now` value.

Use `step_delay_seconds` to slow down form actions when Arctic Shift needs more time.

## Input Files

Put one subreddit per line in `inputs/subreddits.txt`.

```text
AskReddit
science
```

Put one username per line in `inputs/users.txt`.

```text
spez
```

Blank lines and lines starting with `#` are ignored.

## Run

```bash
arctic-harvester --config config.toml
```

Or run it as a module.

```bash
python -m arctic_harvester.cli --config config.toml
```

## Completion Logic

ArcticHarvester does not watch the download folder. Arctic Shift writes through the save picker, not a normal browser download event.

Instead, it waits until Arctic Shift shows `New download` or `Download complete`. That is the page signal that writing has finished.

## Troubleshooting

If later items do not start, increase `step_delay_seconds`.

If large downloads time out, increase `download_timeout_seconds`.

If Arctic Shift changes its page layout, selectors in `arctic_harvester/page.py` may need updates.
