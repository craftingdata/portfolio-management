#!/usr/bin/env python3
"""Unit economics helper (dependency-free).

Purpose: quick, back-of-the-envelope calculations for business evaluation.

Outputs:
- gross margin ($ and %)
- CAC payback months
- simple LTV (gross margin basis) using churn per month (optional)
- LTV:CAC ratio (optional)

Notes:
- Uses Decimal for financial precision.
- This is a heuristic tool; ranges and judgment still matter.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, getcontext


getcontext().prec = 28


def _d(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"Invalid decimal: {value}") from exc


@dataclass(frozen=True)
class Inputs:
    arpa: Decimal
    cogs: Decimal
    cac: Decimal
    churn_per_month: Decimal | None


@dataclass(frozen=True)
class Outputs:
    gross_margin_dollars: Decimal
    gross_margin_pct: Decimal
    payback_months: Decimal | None
    ltv_gm_basis: Decimal | None
    ltv_to_cac: Decimal | None


def compute(inputs: Inputs) -> Outputs:
    if inputs.arpa <= 0:
        raise ValueError("ARPA must be > 0")
    if inputs.cogs < 0:
        raise ValueError("COGS must be >= 0")
    if inputs.cac < 0:
        raise ValueError("CAC must be >= 0")

    gross_margin_dollars = inputs.arpa - inputs.cogs
    gross_margin_pct = gross_margin_dollars / inputs.arpa

    payback_months: Decimal | None
    if gross_margin_dollars > 0 and inputs.cac > 0:
        payback_months = inputs.cac / gross_margin_dollars
    else:
        payback_months = None

    ltv_gm_basis: Decimal | None = None
    ltv_to_cac: Decimal | None = None

    if inputs.churn_per_month is not None:
        churn = inputs.churn_per_month
        if churn <= 0:
            raise ValueError("churn_per_month must be > 0 when provided")
        ltv_gm_basis = gross_margin_dollars / churn
        if inputs.cac > 0:
            ltv_to_cac = ltv_gm_basis / inputs.cac

    return Outputs(
        gross_margin_dollars=gross_margin_dollars,
        gross_margin_pct=gross_margin_pct,
        payback_months=payback_months,
        ltv_gm_basis=ltv_gm_basis,
        ltv_to_cac=ltv_to_cac,
    )


def _fmt_money(x: Decimal) -> str:
    return f"{x.quantize(Decimal('0.01'))}"


def _fmt_pct(x: Decimal) -> str:
    return f"{(x * Decimal('100')).quantize(Decimal('0.01'))}%"


def main() -> int:
    parser = argparse.ArgumentParser(description="Unit economics quick calculator")
    parser.add_argument(
        "--arpa",
        required=True,
        type=_d,
        help="Average revenue per account (per month)",
    )
    parser.add_argument(
        "--cogs",
        required=True,
        type=_d,
        help="Variable costs per account (per month)",
    )
    parser.add_argument(
        "--cac",
        required=True,
        type=_d,
        help="Customer acquisition cost (per customer)",
    )
    parser.add_argument(
        "--churn-per-month",
        type=_d,
        default=None,
        help="Monthly churn rate as a decimal (e.g., 0.05 for 5%)",
    )

    args = parser.parse_args()

    outputs = compute(
        Inputs(
            arpa=args.arpa,
            cogs=args.cogs,
            cac=args.cac,
            churn_per_month=args.churn_per_month,
        )
    )

    print("Inputs")
    print(f"  ARPA: {_fmt_money(args.arpa)}")
    print(f"  COGS: {_fmt_money(args.cogs)}")
    print(f"  CAC:  {_fmt_money(args.cac)}")
    if args.churn_per_month is not None:
        print(f"  Churn/month: {_fmt_pct(args.churn_per_month)}")

    print("\nOutputs")
    print(f"  Gross margin ($): {_fmt_money(outputs.gross_margin_dollars)}")
    print(f"  Gross margin (%): {_fmt_pct(outputs.gross_margin_pct)}")

    if outputs.payback_months is None:
        print("  CAC payback (months): n/a")
    else:
        print(
            f"  CAC payback (months): {outputs.payback_months.quantize(Decimal('0.01'))}"
        )

    if outputs.ltv_gm_basis is not None:
        print(f"  Simple LTV (GM basis): {_fmt_money(outputs.ltv_gm_basis)}")
    if outputs.ltv_to_cac is not None:
        print(f"  LTV:CAC: {outputs.ltv_to_cac.quantize(Decimal('0.01'))}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
