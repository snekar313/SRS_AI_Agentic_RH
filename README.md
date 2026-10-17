# BB Options Analyzer

A read-only command-line tool for analyzing exported BlackBerry (`BB`) option
activity. It calculates realized option profit/loss, fees, expiration and
assignment events, and positions that remain open.

The analyzer never connects to a brokerage and cannot place, modify, or cancel
orders. Export activity from an authenticated Robinhood session, remove account
identifiers, and provide it as CSV.

## Requirements

- Python 3.11 or newer

The application has no third-party runtime dependencies.

## Input format

CSV columns:

```text
symbol,expiration,strike,option_type,action,quantity,price,fees,executed_at
```

Supported actions are `buy_to_open`, `sell_to_close`, `sell_to_open`,
`buy_to_close`, `expiration`, and `assignment`. Prices are per share; the tool
uses the standard option multiplier of 100. Dates use ISO 8601. Expiration and
assignment rows use a price of `0` and close the specified quantity.

Example:

```csv
symbol,expiration,strike,option_type,action,quantity,price,fees,executed_at
BB,2026-09-18,4.00,call,buy_to_open,2,0.35,0.02,2026-09-02T10:15:00-04:00
BB,2026-09-18,4.00,call,sell_to_close,2,0.60,0.02,2026-09-10T14:30:00-04:00
```

## Run

```bash
python -m bb_options_analyzer activity.csv --start 2026-09-01 --end 2026-09-30
```

The output is JSON so it can be reviewed directly or used by another agent.

## Test

```bash
python -m unittest discover -s tests -v
```

Calculations cover the option contract only. Assignment-related stock proceeds,
tax treatment, regulatory charges not included in the export, and corporate
actions require separate brokerage records.
