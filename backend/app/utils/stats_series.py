"""将按日聚合结果填充为连续日期序列（欢迎页图表）"""
from datetime import date, timedelta
from typing import Callable, Iterable


def build_daily_series(
    start_date: date,
    days: int,
    daily_map: dict[str, dict],
    *,
    defaults: dict | None = None,
) -> list[dict]:
    """daily_map: iso date -> {field: value, ...}"""
    base = dict(defaults or {})
    series: list[dict] = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        key = d.isoformat()
        row = {"date": key, **base}
        if key in daily_map:
            row.update(daily_map[key])
        series.append(row)
    return series


def rows_to_map(rows: Iterable, key_fn: Callable, value_fn: Callable) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for row in rows:
        k = key_fn(row)
        out[k] = value_fn(row)
    return out
