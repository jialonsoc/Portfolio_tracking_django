from collections import defaultdict
from datetime import date
from decimal import Decimal

from portfolios.models import Holding, Portfolio, Price

def portfolio_value_series(
    *,
    portfolio: Portfolio,
    fecha_inicio: date,
    fecha_fin: date) -> list[dict]:
    """V_t = sum_i c_i,t * p_i,t"""
    holdings = list(
        Holding.objects.filter(portfolio=portfolio).select_related("asset")
    )
    qty_by_asset = {h.asset_id: h.quantity for h in holdings}
    asset_ids =list(qty_by_asset.keys())
    prices = Price.objects.filter(
        asset_id__in=asset_ids,
        date__gte=fecha_inicio,
        date__lte=fecha_fin,

    ).values("asset_id", "date", "value")
    totals = defaultdict(lambda: Decimal("0.0"))
    for p in prices:
        totals[p["date"]] += Decimal(p["value"])*qty_by_asset[p["asset_id"]]

    return [
        {"date": d.isoformat(), "value": v} for d, v in sorted(totals.items())
    ]

def portfolio_weight_series(
    *,
    portfolio: Portfolio,
    fecha_inicio: date,
    fecha_fin: date) -> list[dict]:
    """w_i,t = c_i,t * p_i,t / V_t"""

    holdings = list(
        Holding.objects.filter(portfolio=portfolio).select_related("asset")
    )
    qty_by_asset = {h.asset_id : h.quantity for h in holdings}
    name_by_id = {h.asset_id: h.asset.name for h in holdings}
    asset_ids = list(qty_by_asset.keys())

    prices = Price.objects.filter(
        asset_id__in=asset_ids,
        date__gte=fecha_inicio,
        date__lte=fecha_fin
    ).values("asset_id", "date", "value")

    amounts = defaultdict(dict)
    for p in prices:
        amounts[p["date"]][p["asset_id"]] = (Decimal(p["value"])* qty_by_asset[p["asset_id"]])

    series = []
    for d, by_asset in sorted(amounts.items()):
        v_t = sum(by_asset.values())
        if v_t == 0:
            continue
        series.append(
            {
                "date": d.isoformat(),
                "portfolio_value": str(v_t),
                "weights": {name_by_id[aid]: str(x/v_t) for aid, x in by_asset.items()
                },
            }
        )

    return series
