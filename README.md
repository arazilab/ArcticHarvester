![ArcticHarvester banner](assets/banner.png)

# ArcticHarvester

ArcticHarvester batch downloads Reddit data through the Arctic Shift download tool.

It opens Chrome or Edge with Selenium, fills the Arctic Shift form, starts the download, waits for the downloaded file, then refreshes the page and moves to the next item.

## What It Does

- Reads subreddit names from `inputs/subreddits.txt`
- Reads usernames from `inputs/users.txt`
- Skips an input file when it is empty
- Uses `r/name` for subreddits and `u/name` for users
- Sets start and end dates from `config.toml`
- Leaves start date empty when you want Arctic Shift to use its earliest available date
- Uses today as the end date when no end date is set
- Downloads posts, comments, or both
- Waits between downloads using a configurable delay

## Requirements

- Python 3.11 or newer
- Google Chrome or Microsoft Edge installed
- Internet access

Selenium uses the browser selected in `config.toml`.

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
```

Use `browser = "edge"` if you want Microsoft Edge.

Dates must use `YYYY-MM-DD`.

When `start_date` is empty, Arctic Shift should use the earliest available date after the subreddit or user is entered.

When `end_date` is empty, ArcticHarvester uses today's date.

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

You can also write `r/AskReddit` or `u/spez`. Blank lines are ignored.

## Run

```bash
arctic-harvester --config config.toml
```

Or run it as a module.

```bash
python -m arctic_harvester.cli --config config.toml
```

Downloaded files go into `downloads` by default.

## Notes

The tool watches the download folder because Selenium does not expose a standard finished download event. It also checks page progress elements when the page exposes them.

If Arctic Shift changes its page layout, the form finder may need a selector update.

Large subreddits can take a long time. Increase `download_timeout_seconds` for large downloads.
