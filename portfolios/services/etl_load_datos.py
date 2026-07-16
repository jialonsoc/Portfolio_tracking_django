from datetime import date
from decimal import Decimal
from pathlib import Path


import pandas as pd
from django.db import transaction

from portfolios.models import Asset, Portfolio, Price, InitialWeight, Holding

V0 = Decimal("1000000000")
T0 = date(2022, 2, 15)

PORTFOLIO_COLS = {
    "portafolio 1": "Portafolio 1",
    "portafolio 2": "Portafolio 2",
}
@transaction.atomic
def load_datos_xlsx(file_path: str | Path) -> dict:
    path = Path(file_path)
    weights_df = pd.read_excel(path, sheet_name="weights")
    prices_df = pd.read_excel(path, sheet_name="Precios")

    # Activos: como juntamos nuestras tablas 
    asset_names = set(weights_df["activos"].astype(str).str.strip())
    asset_names |= {str(c).strip() for c in prices_df.columns if c != "Dates"}

    assets = {}
    for name in sorted(asset_names):
        asset, _ = Asset.objects.get_or_create(name=name)
        assets[name] = asset

    # Portafolios:
    portfolios = {}
    for col, name in PORTFOLIO_COLS.items():
        portfolio, _ = Portfolio.objects.update_or_create(name=name, defaults ={"initial_value": V0, "start_date": T0})
        portfolios[col] = portfolio

    # Weights:
    InitialWeight.objects.filter(portfolio__in=portfolios.values()).delete()
    # si recargamos el excel eliminamos los pesos iniciales para no tener duplicados, 
    # portfolio__in es un lock para solo los que esten en la lista portfolios
    for _, row in weights_df.iterrows(): #ponemos _ porque no usamos el indice
        asset = assets[str(row["activos"]).strip()] #no podemos poner un string necesitamos la key 
        for col, portfolio in portfolios.items():
            InitialWeight.objects.create(portfolio=portfolio, asset=asset, weight=Decimal(str(row[col])))
    # Precios
    price_cols = [c for c in prices_df.columns if c != "Dates"]
    Price.objects.filter(asset__name__in=price_cols).delete()

    price_objs = []
    for _, row in prices_df.iterrows():
        d = pd.Timestamp(row["Dates"]).date()
        for col in price_cols:
            if pd.isna(row[col]):
                continue
            price_objs.append(
                Price(asset=assets[str(col).strip()],
                date = d,
                value = Decimal(str(row[col])),
                )
            )

    Price.objects.bulk_create(price_objs)
    # Cantidades (holdings) c_i,0 = (w_i,0) * V_0 / p_i,0
    from portfolios.models import Holding

    Holding.objects.filter(portfolio__in=portfolios.values()).delete()
    holdings_count = {}

    for portfolio in portfolios.values():
        count = 0
        for iw in portfolio.initial_weights.select_related("asset"):
            price = Price.objects.get(asset = iw.asset, date = portfolio.start_date)
            qty = (iw.weight * portfolio.initial_value) /  price.value
            Holding.objects.create(
                portfolio=portfolio,
                asset= iw.asset,
                quantity=qty,
            )
            count += 1
        holdings_count[portfolio.name] = count

    return {
        "assets": len(assets),
        "prices": len(price_objs),
        "holdings": holdings_count,   
            }



