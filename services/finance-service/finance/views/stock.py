import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.serializers.stock import StockResponseBodySerializer
from finance.serializers.stock_history import StockHistoryResponseBodySerializer
from finance.views.invest_mixin import InvestmentViewMixin


class StockView(InvestmentViewMixin, APIView):
    def get(self, request):
        code = request.GET.get("code")
        access_token = self.get_access_token()

        url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/search-info"

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {access_token}",
            "appkey": self.invest_app_key,
            "appsecret": self.invest_secret_key,
            "tr_id": "FHKST01010100",
            "custtype": "P"
        }

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": code
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()

            serializer = StockResponseBodySerializer(data)
            return Response(serializer.data)
        else:

            return Response({"error": "Failed to fetch data from Korea Invest API"}, status=500)

class StockHistoryView(InvestmentViewMixin, APIView):
    def get(self, request):
        code = request.GET.get("code")
        start_date = request.GET.get("start_date")  # FID_INPUT_DATE_1
        end_date = request.GET.get("end_date")  # FID_INPUT_DATE_2
        period_div_code = request.GET.get("period_div_code", "D")  # 기본 'D'일봉
        org_adj_prc = request.GET.get("org_adj_prc", "0")  # 기본 수정주가

        if not code or not start_date or not end_date:
            return Response(
                {"error": "Missing required query parameters: code, start_date, end_date"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        access_token = self.get_access_token()

        url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {access_token}",
            "appkey": self.invest_app_key,
            "appsecret": self.invest_secret_key,
            "tr_id": "FHKST03010100",
            "custtype": "P"
        }

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # KRX 고정
            "FID_INPUT_ISCD": code,  # 종목코드
            "FID_INPUT_DATE_1": start_date,  # 조회 시작일
            "FID_INPUT_DATE_2": end_date,  # 조회 종료일
            "FID_PERIOD_DIV_CODE": period_div_code,  # 기간 분류 (D,W,M,Y)
            "FID_ORG_ADJ_PRC": org_adj_prc,  # 수정주가 여부 (0/1)
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()

            serializer = StockHistoryResponseBodySerializer(data)
            return Response(serializer.data)
        else:
            return Response(
                {"error": f"Failed to fetch data from Korea Invest API: {response.status_code}"},
                status=response.status_code,
            )