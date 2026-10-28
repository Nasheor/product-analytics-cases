"""Cost cap and spend ledger for paid model calls.

Every paid call in this repo goes through this module (workspace rule 4). It prices tokens from
``prices.json`` at the repo root, appends one line per call to ``runs/spend.jsonl`` and raises
``BudgetExceeded`` when a run or the repo passes its cap. Prices must be verified against the
official pricing pages before any paid run (``verified: true`` in ``prices.json``).

Environment (loaded from ``../.env`` then ``./.env``, existing variables win):
    ANTHROPIC_API_KEY, OPENROUTER_API_KEY, RUN_COST_CAP_EUR (default 2), REPO_COST_CAP_EUR (default 10),
    USD_TO_EUR (default 0.92), ALLOW_UNVERIFIED_PRICES (default 0).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "runs" / "spend.jsonl"
PRICES = ROOT / "prices.json"


class BudgetExceeded(RuntimeError):
    """A run or the repo has spent more than its cap."""


class PricesUnverified(RuntimeError):
    """prices.json is not marked verified and ALLOW_UNVERIFIED_PRICES is not 1."""


def load_env() -> None:
    """Load ../.env (workspace keys) and ./.env without overriding variables already set."""
    for p in (ROOT.parent / ".env", ROOT / ".env"):
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def _prices() -> dict[str, Any]:
    data = json.loads(PRICES.read_text(encoding="utf-8"))
    if not data.get("verified") and os.environ.get("ALLOW_UNVERIFIED_PRICES", "0") != "1":
        raise PricesUnverified("prices.json is not verified. Check the official pricing pages, fill the table, set verified true.")
    return data


def price_eur(model: str, input_tokens: int, output_tokens: int) -> float:
    """Euro cost of one call from the per-million-token USD prices in prices.json."""
    table = _prices()["usd_per_mtok"]
    if model not in table or table[model].get("in") is None:
        raise PricesUnverified(f"no verified price for model {model!r} in prices.json")
    usd = (input_tokens * table[model]["in"] + output_tokens * table[model]["out"]) / 1_000_000
    return round(usd * float(os.environ.get("USD_TO_EUR", "0.92")), 6)


class Ledger:
    """Append-only spend ledger with a per-run and per-repo cap."""

    def __init__(self, run_id: str | None = None) -> None:
        load_env()
        self.run_id = run_id or dt.datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        self.run_cap = float(os.environ.get("RUN_COST_CAP_EUR", "2"))
        self.repo_cap = float(os.environ.get("REPO_COST_CAP_EUR", "10"))
        LEDGER.parent.mkdir(parents=True, exist_ok=True)

    def _rows(self) -> list[dict[str, Any]]:
        if not LEDGER.exists():
            return []
        return [json.loads(x) for x in LEDGER.read_text(encoding="utf-8").splitlines() if x.strip()]

    def run_total(self) -> float:
        return round(sum(r["eur"] for r in self._rows() if r["run_id"] == self.run_id), 6)

    def repo_total(self) -> float:
        return round(sum(r["eur"] for r in self._rows()), 6)

    def check(self) -> None:
        if self.run_total() > self.run_cap:
            raise BudgetExceeded(f"run {self.run_id} spent €{self.run_total():.4f}, cap €{self.run_cap}")
        if self.repo_total() > self.repo_cap:
            raise BudgetExceeded(f"repo spent €{self.repo_total():.4f}, cap €{self.repo_cap}")

    def record(self, provider: str, model: str, input_tokens: int, output_tokens: int, note: str = "") -> float:
        eur = price_eur(model, input_tokens, output_tokens)
        row = {
            "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "run_id": self.run_id,
            "provider": provider,
            "model": model,
            "in": input_tokens,
            "out": output_tokens,
            "eur": eur,
            "note": note,
        }
        with LEDGER.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        self.check()
        return eur


def messages_create(client: Any, ledger: Ledger, note: str = "", **kwargs: Any) -> Any:
    """Anthropic Messages call through the ledger. ``client`` is anthropic.Anthropic()."""
    ledger.check()
    resp = client.messages.create(**kwargs)
    ledger.record("anthropic", kwargs["model"], resp.usage.input_tokens, resp.usage.output_tokens, note)
    return resp


async def amessages_create(client: Any, ledger: Ledger, note: str = "", **kwargs: Any) -> Any:
    """Async variant for anthropic.AsyncAnthropic()."""
    ledger.check()
    resp = await client.messages.create(**kwargs)
    ledger.record("anthropic", kwargs["model"], resp.usage.input_tokens, resp.usage.output_tokens, note)
    return resp


def openrouter_chat(ledger: Ledger, model: str, messages: list[dict[str, Any]], note: str = "", **kwargs: Any) -> dict[str, Any]:
    """OpenRouter chat completion through the ledger. Returns the JSON body."""
    import httpx

    ledger.check()
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    r = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model, "messages": messages, **kwargs},
        timeout=120,
    )
    r.raise_for_status()
    body = r.json()
    usage = body.get("usage", {})
    ledger.record("openrouter", model, int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0)), note)
    return body
