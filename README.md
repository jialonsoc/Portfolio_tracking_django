# Portafolios de inversión (Django) — V1

Proyecto Django que modela dos portafolios, carga datos desde `datos.xlsx`, calcula cantidades iniciales \(c_{i,0}\) y expone una API REST + dashboard para la evolución de \(w_{i,t}\) y \(V_t\).

Arquitectura inspirada en [HackSoftware Django Styleguide](https://github.com/HackSoftware/Django-Styleguide):

- **Models**: datos persistidos
- **Services**: escritura / ETL
- **Selectors**: lectura + cálculos derivados
- **APIs / Views**: interfaces delgadas (sin lógica de negocio)

---

## Definiciones del dominio

\[
V_t = \sum_{i=1}^{N} x_{i,t}, \quad
x_{i,t} = p_{i,t} \cdot c_{i,t}, \quad
w_{i,t} = \frac{x_{i,t}}{V_t}
\]

Cantidad inicial:

\[
c_{i,0} = \frac{w_{i,0} \cdot V_0}{p_{i,0}}
\]

Supuesto del enunciado: a partir de \(t=0\), \(c_{i,t} = c_{i,0}\) (cantidades fijas).  
\(V_0 = 1{,}000{,}000{,}000\) al `2022-02-15`.

**Qué se guarda vs qué se calcula**

| Concepto | Persistido | Motivo |
|----------|------------|--------|
| Activo, Portafolio | Sí | Catálogo / configuración |
| \(p_{i,t}\) | Sí | Serie histórica (Excel) |
| \(w_{i,0}\) | Sí | Solo existe en \(t=0\) |
| \(c_{i,0}\) | Sí | Se calcula una vez y queda fija |
| \(x_{i,t}\), \(w_{i,t}\), \(V_t\) | No | Se derivan con precios + holdings |

---

## Setup

```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1

pip install django djangorestframework openpyxl pandas
python manage.py migrate
python manage.py load_datos
python manage.py runserver
```

- Dashboard: http://127.0.0.1:8000/
- API values: `/api/portfolios/<id>/values/?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD`
- API weights: `/api/portfolios/<id>/weights/?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD`

---

## Estructura del proyecto

```
V1/
├── manage.py
├── datos.xlsx
├── config/                         # settings del proyecto Django
│   ├── settings.py
│   ├── urls.py                     # include de portfolios.urls
│   ├── wsgi.py / asgi.py
└── portfolios/                     # app de dominio
    ├── models.py                   # Asset, Portfolio, Price, InitialWeight, Holding
    ├── apis.py                     # endpoints DRF
    ├── views.py                    # DashboardView (HTML)
    ├── urls.py                     # rutas de la app
    ├── services/
    │   └── etl_load_datos.py       # ETL + cálculo c_i,0
    ├── selectors/
    │   └── portfolio_evolution.py  # series V_t y w_i,t
    ├── management/commands/
    │   └── load_datos.py           # python manage.py load_datos
    └── templates/portfolios/
        └── dashboard.html          # gráficos Chart.js
```

Flujo de datos:

```
datos.xlsx
  service ETL (load_datos)
  BD (Asset, Portfolio, Price, InitialWeight, Holding)
  selectors (cálculo V_t / w_i,t)
  APIs REST
  dashboard (fetch + Chart.js) **Hecho con IA**
```

---

## Modelos (`portfolios/models.py`)

### `Asset`

Activo invertible \(i\) (EEUU, Europa, Tesoro, …).  
Campo principal: `name` (único).

### `Portfolio`

Portafolio con:

- `name`
- `initial_value`: \(V_0\)
- `start_date`: fecha \(t=0\)

### `Price`

Precio \(p_{i,t}\):

- FK a `Asset` (`related_name="prices"`)
- `date`, `value`
- `unique_together = (asset, date)`

### `InitialWeight`

Weight inicial \(w_{i,0}\):

- FK a `Portfolio` (`related_name="initial_weights"`)
- FK a `Asset`
- `weight`
- único por `(portfolio, asset)`

### `Holding`

Cantidad \(c_{i,0}\) (invariante en el tiempo):

- FK a `Portfolio` (`related_name="holdings"`)
- FK a `Asset`
- `quantity`
- único por `(portfolio, asset)`

`related_name` permite navegar al revés, por ejemplo:  
`portfolio.holdings.all()`, `portfolio.initial_weights.all()`.

---

## Service / ETL (`portfolios/services/etl_load_datos.py`)

Comando: `python manage.py load_datos`

1. Lee hoja `weights` después crea `Asset`, `Portfolio`, `InitialWeight`
2. Lee hoja `Precios` después crea `Price` (`bulk_create`)
3. Calcula y guarda `Holding`:

\[
c_{i,0} = \frac{w_{i,0} \cdot V_0}{p_{i,0}}
\]

Usa `@transaction.atomic` para no dejar la BD a medias si falla.

---

## Selectors (`portfolios/selectors/portfolio_evolution.py`)

Los selectors **leen** con el ORM y calculan series. No escriben en BD.

### `portfolio_value_series(portfolio, fecha_inicio, fecha_fin)`

1. Obtiene holdings del portafolio (`c_{i,0}`)
2. Filtra precios en el rango de fechas
3. Por cada fecha \(t\): \(V_t = \sum_i p_{i,t} \cdot c_{i,0}\)
4. Devuelve `[{date, value}, ...]`

### `portfolio_weight_series(portfolio, fecha_inicio, fecha_fin)`

1. Mismo uso de holdings + precios
2. Por fecha: \(x_{i,t} = p_{i,t} \cdot c_{i,0}\)
3. \(V_t = \sum_i x_{i,t}\)
4. \(w_{i,t} = x_{i,t} / V_t\)
5. Devuelve `[{date, portfolio_value, weights: {activo: w}}, ...]`

Detalle:

- `select_related("asset")` evita N+1
- `.values(...)` trae solo columnas necesarias

## APIs (`portfolios/apis.py`)

Patrón:

1. Validar query params (`fecha_inicio`, `fecha_fin`) con serializer
2. Obtener portafolio (`get_object_or_404`)
3. Llamar al selector
4. Devolver JSON

### `DateRangeQuerySerializer`

Valida que ambas fechas existan y que `fecha_inicio <= fecha_fin`.

### `GET /api/portfolios/<portfolio_id>/values/`

Respuesta:

```json
{
  "portfolio": "Portafolio 1",
  "fecha_inicio": "2022-02-15",
  "fecha_fin": "2022-02-28",
  "series": [
    {"date": "2022-02-15", "value": "1000000000.00"}
  ]
}
```

### `GET /api/portfolios/<portfolio_id>/weights/`

Respuesta:

```json
{
  "portfolio": "Portafolio 1",
  "fecha_inicio": "2022-02-15",
  "fecha_fin": "2022-02-28",
  "series": [
    {
      "date": "2022-02-15",
      "portfolio_value": "1000000000.00",
      "weights": {"EEUU": "0.28", "Europa": "0.087"}
    }
  ]
}
```

---

## URLs

### `config/urls.py`

Incluye las rutas de la app:

```python
path("", include("portfolios.urls"))
```

### `portfolios/urls.py`

| Ruta | Vista | Descripción |
|------|-------|-------------|
| `/` | `DashboardView` | UI con gráficos |
| `/api/portfolios/<id>/values/` | `PortfolioValueApi` | Serie \(V_t\) |
| `/api/portfolios/<id>/weights/` | `PortfolioWeightApi` | Serie \(w_{i,t}\) |

---

## Dashboard (`views.py` + template)

`DashboardView` solo prepara contexto:

- lista de portafolios (`portfolios_json`)
- fechas por defecto

El template (`dashboard.html`):

1. Hace `fetch` a las APIs `/values/` y `/weights/`
2. Grafica \(V_t\) como **línea**
3. Grafica \(w_{i,t}\) como **stacked area** (Chart.js)

No recalcula en el frontend: consume la API.

---

## Ejemplo de uso API

```
/api/portfolios/1/values/?fecha_inicio=2022-02-15&fecha_fin=2022-02-28
/api/portfolios/1/weights/?fecha_inicio=2022-02-15&fecha_fin=2022-02-28
/api/portfolios/2/weights/?fecha_inicio=2022-02-15&fecha_fin=2023-02-16
```


