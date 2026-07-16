from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from portfolios.models import Portfolio
from portfolios.selectors.portfolio_evolution import portfolio_value_series, portfolio_weight_series

class DateRangeQuerySerializer(serializers.Serializer):
    fecha_inicio = serializers.DateField(required=True)
    fecha_fin = serializers.DateField(required=True)

    def validate(self, attrs):
        if attrs["fecha_inicio"] > attrs["fecha_fin"]:
            raise serializers.ValidationError("La fecha de inicio debe ser anterior a la fecha de fin")

        return attrs

class PortfolioValueApi(APIView):
    def get(self, request, portfolio_id: int):
        portfolio = get_object_or_404(Portfolio, pk=portfolio_id)
        query = DateRangeQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        series = portfolio_value_series(
            portfolio=portfolio,
            fecha_inicio=query.validated_data["fecha_inicio"],
            fecha_fin=query.validated_data["fecha_fin"],
        )

        return Response(
            {
                "portfolio": portfolio.name,
                "fecha_inicio": query.validated_data["fecha_inicio"].isoformat(),
                "fecha_fin": query.validated_data["fecha_fin"].isoformat(),
                "series": series,
            }
        )

class PortfolioWeightApi(APIView):
    def get(self, request, portfolio_id: int):
        portfolio = get_object_or_404(Portfolio, pk=portfolio_id)
        query = DateRangeQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        series = portfolio_weight_series(
            portfolio=portfolio,
            fecha_inicio=query.validated_data["fecha_inicio"],
            fecha_fin=query.validated_data["fecha_fin"],
        )
        return Response(
            {
                "portfolio": portfolio.name,
                "fecha_inicio": query.validated_data["fecha_inicio"].isoformat(),
                "fecha_fin": query.validated_data["fecha_fin"].isoformat(),
                "series": series,
            }
        )
        

