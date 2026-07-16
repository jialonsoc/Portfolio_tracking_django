from django.urls import path
from portfolios.apis import PortfolioValueApi, PortfolioWeightApi
from portfolios.views import DashboardView
urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("api/portfolios/<int:portfolio_id>/values/", PortfolioValueApi.as_view(), name="api-portfolio-values"),
    path("api/portfolios/<int:portfolio_id>/weights/", PortfolioWeightApi.as_view(), name="api-portfolio-weights"),
]