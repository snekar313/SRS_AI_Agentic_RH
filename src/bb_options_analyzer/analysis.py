from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable, Mapping


MULTIPLIER = Decimal("100")
OPEN_ACTIONS = {"buy_to_open": 1, "sell_to_open": -1}
CLOSE_ACTIONS = {"sell_to_close": 1, "buy_to_close": -1}
TERMINAL_ACTIONS = {"expiration", "assignment"}


@dataclass
class Position:
    quantity: int = 0
    net_cash: Decimal = Decimal("0")


def _money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'))}"


def _contract(row: Mapping[str, str]) -> tuple[str, str, str, str]:
    return (
        row["symbol"].upper(),
        row["expiration"],
        f"{Decimal(row['strike']):.2f}",
        row["option_type"].lower(),
    )


def _label(key: tuple[str, str, str, str]) -> str:
    symbol, expiration, strike, option_type = key
    return f"{symbol} {expiration} {strike} {option_type}"


def analyze_rows(
    rows: Iterable[Mapping[str, str]],
    start: date,
    end: date,
    symbol: str = "BB",
) -> dict[str, object]:
    if start > end:
        raise ValueError("start date must not be after end date")

    selected = []
    for row in rows:
        executed = datetime.fromisoformat(row["executed_at"])
        if row["symbol"].upper() == symbol.upper() and executed.date() <= end:
            selected.append((executed, row))
    selected.sort(key=lambda item: item[0])

    positions: defaultdict[tuple[str, str, str, str], Position] = defaultdict(Position)
    realized = Decimal("0")
    fees = Decimal("0")
    closed_contracts = 0
    events: list[dict[str, object]] = []
    activity_rows = 0

    for executed, row in selected:
        in_period = start <= executed.date() <= end
        key = _contract(row)
        action = row["action"].lower()
        quantity = int(row["quantity"])
        price = Decimal(row["price"])
        fee = Decimal(row.get("fees") or "0")
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if action not in OPEN_ACTIONS.keys() | CLOSE_ACTIONS.keys() | TERMINAL_ACTIONS:
            raise ValueError(f"unsupported action: {action}")

        position = positions[key]
        if in_period:
            fees += fee
            activity_rows += 1

        if action in OPEN_ACTIONS:
            direction = OPEN_ACTIONS[action]
            if position.quantity and (position.quantity > 0) != (direction > 0):
                raise ValueError(f"opening action reverses existing position for {_label(key)}")
            cash = price * MULTIPLIER * quantity
            position.quantity += direction * quantity
            position.net_cash += (-cash if direction > 0 else cash) - fee
            continue

        if not position.quantity:
            raise ValueError(f"closing action without an open position for {_label(key)}")
        direction = 1 if position.quantity > 0 else -1
        if action in CLOSE_ACTIONS and CLOSE_ACTIONS[action] != direction:
            raise ValueError(f"closing action does not match position for {_label(key)}")
        if quantity > abs(position.quantity):
            raise ValueError(f"closing quantity exceeds open position for {_label(key)}")

        cash = price * MULTIPLIER * quantity
        close_cash = cash if direction > 0 else -cash
        allocation = position.net_cash * Decimal(quantity) / Decimal(abs(position.quantity))
        trade_realized = allocation + close_cash - fee
        if in_period:
            realized += trade_realized
            closed_contracts += quantity
        position.net_cash -= allocation
        position.quantity -= direction * quantity

        if in_period and action in TERMINAL_ACTIONS:
            events.append(
                {
                    "type": action,
                    "contract": _label(key),
                    "quantity": quantity,
                    "executed_at": executed.isoformat(),
                    "option_realized_pl": _money(trade_realized),
                }
            )

    open_positions = []
    for key, position in sorted(positions.items()):
        if position.quantity:
            open_positions.append(
                {
                    "contract": _label(key),
                    "side": "long" if position.quantity > 0 else "short",
                    "quantity": abs(position.quantity),
                    "net_opening_cash": _money(position.net_cash),
                }
            )

    return {
        "symbol": symbol.upper(),
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "activity_rows": activity_rows,
        "closed_contracts": closed_contracts,
        "realized_option_pl": _money(realized),
        "fees": _money(fees),
        "events": events,
        "open_positions": open_positions,
        "limitations": [
            "Assignment stock proceeds and tax effects are excluded.",
            "Results depend on complete and correctly classified exported activity.",
        ],
    }
