from __future__ import annotations

import os
import time
from typing import Dict, List, Optional, Any

import pandas as pd
import httpx

from backtest.loaders.base import cached_loader_fetch, check_budget, retry_with_budget, validate_date_range
from backtest.loaders.registry import register


def _get_env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _build_headers() -> dict[str, str]:
    token = os.getenv("CUSTOM_DATA_TOKEN", "").strip()
    if not token:
        return {}
    if token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1].strip()
    header = os.getenv("CUSTOM_DATA_TOKEN_HEADER", "Authorization").strip() or "Authorization"
    prefix = os.getenv("CUSTOM_DATA_TOKEN_PREFIX", "Bearer ")
    if not prefix:
        prefix = "Bearer "
    if not prefix.endswith(" "):
        prefix = f"{prefix} "
    return {header: f"{prefix}{token}"}


def _normalize_response_to_frame(
    payload: Any,
    *,
    requested_fields: list[str] | None,
) -> Optional[pd.DataFrame]:
    rows: Any = payload
    if isinstance(payload, dict):
        for key in ("data", "bars", "items", "result"):
            if key in payload:
                rows = payload[key]
                break

    if rows is None:
        return None

    if isinstance(rows, list) and rows and isinstance(rows[0], (list, tuple)):
        cols = ["trade_date", "open", "high", "low", "close", "volume"]
        rows = [dict(zip(cols, r[: len(cols)])) for r in rows]

    if not isinstance(rows, list) or not rows:
        return None

    df = pd.DataFrame(rows)
    if df.empty:
        return None

    dt_col = None
    for c in ("trade_date", "date", "dt", "datetime", "timestamp", "ts"):
        if c in df.columns:
            dt_col = c
            break
    if dt_col is None:
        raise ValueError(f"custom loader response missing datetime column, got columns={list(df.columns)}")

    if dt_col in ("timestamp", "ts"):
        df[dt_col] = pd.to_datetime(pd.to_numeric(df[dt_col], errors="coerce"), unit="ms", utc=True).dt.tz_convert(None)
    else:
        df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")

    df = df.dropna(subset=[dt_col]).sort_values(dt_col)
    df = df.set_index(dt_col)

    rename_map = {"vol": "volume"}
    for src, dst in rename_map.items():
        if src in df.columns and dst not in df.columns:
            df = df.rename(columns={src: dst})

    base_cols = ["open", "high", "low", "close", "volume"]
    for col in base_cols:
        if col not in df.columns:
            raise ValueError(f"custom loader response missing required column {col!r}, got columns={list(df.columns)}")
        df[col] = pd.to_numeric(df[col], errors="coerce")

    keep = list(base_cols)
    if requested_fields:
        for f in requested_fields:
            if f in df.columns and f not in keep:
                keep.append(f)
    df = df[keep].dropna(subset=["open", "high", "low", "close"])
    return df if not df.empty else None


def _strip_date(d: str) -> str:
    return d.replace("-", "").strip()


@register
class DataLoader:
    name = "custom"
    markets = {"a_share"}
    requires_auth = False

    def is_available(self) -> bool:
        daily_url = os.getenv("CUSTOM_DATA_DAILY_URL", "").strip()
        base_url = os.getenv("CUSTOM_DATA_BASE_URL", "").strip()
        if not daily_url and not base_url:
            return False
        if _get_env_bool("CUSTOM_DATA_REQUIRE_AUTH", False):
            return bool(os.getenv("CUSTOM_DATA_TOKEN", "").strip())
        return True

    def __init__(self) -> None:
        daily_url = os.getenv("CUSTOM_DATA_DAILY_URL", "").strip()
        base_url = os.getenv("CUSTOM_DATA_BASE_URL", "").strip().rstrip("/")
        if not daily_url and not base_url:
            raise RuntimeError("CUSTOM_DATA_DAILY_URL or CUSTOM_DATA_BASE_URL is required for custom loader")
        self._daily_url = daily_url
        self._base_url = base_url
        self._bars_path = os.getenv(
            "CUSTOM_DATA_BARS_PATH",
            "/api/open/v1/tushare_daily/get_daily_data",
        ).strip() or "/api/open/v1/tushare_daily/get_daily_data"
        self._url_template = os.getenv("CUSTOM_DATA_URL_TEMPLATE", "").strip()
        self._daily_method = os.getenv("CUSTOM_DATA_DAILY_METHOD", "GET").strip().upper() or "GET"
        self._timeout_s = float(os.getenv("CUSTOM_DATA_TIMEOUT_S", "15"))
        self._budget_s = float(os.getenv("CUSTOM_DATA_FETCH_BUDGET_S", "60"))
        self._headers = _build_headers()

    def fetch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        *,
        interval: str = "1D",
        fields: Optional[List[str]] = None,
    ) -> Dict[str, pd.DataFrame]:
        validate_date_range(start_date, end_date)

        result: Dict[str, pd.DataFrame] = {}
        for code in codes:
            try:
                df = cached_loader_fetch(
                    source=self.name,
                    symbol=code,
                    timeframe=interval,
                    start_date=start_date,
                    end_date=end_date,
                    fields=list(fields or []),
                    fetch=lambda code=code: self._fetch_one(code, start_date, end_date, interval, fields),
                )
                if df is not None and not df.empty:
                    result[code] = df
            except Exception as exc:
                print(f"[WARN] failed to fetch {code}: {exc}")
        return result

    def _fetch_one(
        self,
        code: str,
        start_date: str,
        end_date: str,
        interval: str,
        fields: Optional[List[str]],
    ) -> Optional[pd.DataFrame]:
        if interval != "1D":
            print(f"[WARN] custom loader only supports 1D currently, got {interval}; falling back")
            return None

        deadline = time.monotonic() + self._budget_s
        label = f"custom fetch for {code}"

        def _do_request() -> Any:
            check_budget(deadline, label, budget_s=self._budget_s)
            params = {"code": code, "start_date": start_date, "end_date": end_date}
            if fields:
                params["fields"] = ",".join(fields)

            if self._daily_url:
                url = self._daily_url
            elif self._url_template:
                url = self._url_template.format(
                    base_url=self._base_url,
                    code=code,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                    fields=",".join(fields) if fields else "",
                )
            else:
                url = f"{self._base_url}{self._bars_path}"

            with httpx.Client(timeout=self._timeout_s) as client:
                method = self._daily_method
                try:
                    if method == "GET":
                        resp = client.get(url, params=None if self._url_template else params, headers=self._headers)
                    else:
                        resp = client.request(method, url, json=params, headers=self._headers)
                    resp.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    if method == "GET" and exc.response is not None and exc.response.status_code == 405:
                        resp = client.post(url, json=params, headers=self._headers)
                        resp.raise_for_status()
                    else:
                        raise
                return resp.json()

        payload = retry_with_budget(
            _do_request,
            transient=(httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError),
            deadline=deadline,
            label=label,
        )
        return _normalize_response_to_frame(payload, requested_fields=list(fields or []))
