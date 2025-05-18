import requests
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.serializers.financial_data import FinancialDataResponseBodySerializer
from finance.views.invest_mixin import InvestmentViewMixin


class FinancialDataView(InvestmentViewMixin, APIView):
    def get(self, request):
        code = request.GET.get("code")
        period_code = request.GET.get("period_code", 0)
        market_code = request.GET.get("market_code", "J")
        access_token = self.get_access_token()

        url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/finance/balance-sheet"

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {access_token}",
            "appkey": self.invest_app_key,
            "appsecret": self.invest_secret_key,
            "tr_id": "FHKST66430100",
            "custtype": "P"
        }

        params = {
            "FID_DIV_CLS_CODE": period_code,
            "FID_COND_MRKT_DIV_CODE": market_code,
            "FID_INPUT_ISCD": code
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()

            serializer = FinancialDataResponseBodySerializer(data)
            return Response(serializer.data)

        else:
            return Response({"error": "Failed to fetch data from Korea Invest API"}, status=500)