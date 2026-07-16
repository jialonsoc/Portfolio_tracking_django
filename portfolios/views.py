from django.views.generic import TemplateView
from portfolios.models import Portfolio


class DashboardView(TemplateView):
    template_name = "portfolios/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Portfolio.objects.all().order_by("name")
        context["portfolios_json"] = [{"id": p.id, "name": p.name} for p in qs]
        context["default_start"] = "2022-02-15"
        context["default_end"] = "2023-02-16"
        return context