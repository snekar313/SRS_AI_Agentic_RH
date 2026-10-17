import unittest
from datetime import date

from bb_options_analyzer import analyze_rows


def row(action, quantity, price, when, fees="0.00", option_type="call"):
    return {
        "symbol": "BB",
        "expiration": "2026-09-18",
        "strike": "4",
        "option_type": option_type,
        "action": action,
        "quantity": str(quantity),
        "price": str(price),
        "fees": fees,
        "executed_at": when,
    }


class AnalyzeRowsTests(unittest.TestCase):
    def test_long_round_trip_includes_fees(self):
        result = analyze_rows(
            [
                row("buy_to_open", 2, "0.35", "2026-09-02T10:15:00-04:00", "0.02"),
                row("sell_to_close", 2, "0.60", "2026-09-10T14:30:00-04:00", "0.02"),
            ],
            date(2026, 9, 1),
            date(2026, 9, 30),
        )
        self.assertEqual(result["realized_option_pl"], "49.96")
        self.assertEqual(result["fees"], "0.04")
        self.assertEqual(result["open_positions"], [])

    def test_expired_long_realizes_remaining_cost(self):
        result = analyze_rows(
            [
                row("buy_to_open", 1, "0.25", "2026-09-02T10:15:00-04:00"),
                row("expiration", 1, "0", "2026-09-18T16:00:00-04:00"),
            ],
            date(2026, 9, 1),
            date(2026, 9, 30),
        )
        self.assertEqual(result["realized_option_pl"], "-25.00")
        self.assertEqual(result["events"][0]["type"], "expiration")

    def test_short_assignment_preserves_option_premium(self):
        result = analyze_rows(
            [
                row("sell_to_open", 1, "0.40", "2026-09-02T10:15:00-04:00"),
                row("assignment", 1, "0", "2026-09-18T16:00:00-04:00"),
            ],
            date(2026, 9, 1),
            date(2026, 9, 30),
        )
        self.assertEqual(result["realized_option_pl"], "40.00")
        self.assertEqual(result["events"][0]["type"], "assignment")

    def test_reports_remaining_position_and_filters_dates(self):
        result = analyze_rows(
            [
                row("buy_to_open", 1, "0.10", "2026-08-31T12:00:00-04:00"),
                row("buy_to_open", 3, "0.20", "2026-09-05T12:00:00-04:00"),
            ],
            date(2026, 9, 1),
            date(2026, 9, 30),
        )
        self.assertEqual(result["activity_rows"], 1)
        self.assertEqual(result["open_positions"][0]["quantity"], 4)

    def test_period_close_uses_position_opened_before_period(self):
        result = analyze_rows(
            [
                row("buy_to_open", 1, "0.10", "2026-08-31T12:00:00-04:00"),
                row("sell_to_close", 1, "0.30", "2026-09-05T12:00:00-04:00"),
            ],
            date(2026, 9, 1),
            date(2026, 9, 30),
        )
        self.assertEqual(result["activity_rows"], 1)
        self.assertEqual(result["realized_option_pl"], "20.00")
        self.assertEqual(result["open_positions"], [])


if __name__ == "__main__":
    unittest.main()
