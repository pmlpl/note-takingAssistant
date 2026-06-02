from datetime import date

from app.utils.stats_series import build_daily_series


def test_build_daily_series_fills_gaps():
    start = date(2026, 5, 1)
    daily_map = {
        "2026-05-01": {"new_users": 2},
        "2026-05-03": {"new_users": 1},
    }
    series = build_daily_series(start, 3, daily_map, defaults={"new_users": 0})
    assert len(series) == 3
    assert series[0]["new_users"] == 2
    assert series[1]["new_users"] == 0
    assert series[2]["new_users"] == 1
