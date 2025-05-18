from datetime import datetime, timedelta

import certifi
import requests
from rest_framework.response import Response
from rest_framework.views import APIView

from market_service import settings

EXCHANGE_RATE_API_KEY = settings.EXCHANGE_RATE_API_KEY

class ExchangeRateView(APIView):
    def get(self, request):
        base_url = "https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"
        results = []

        # 오늘 날짜 기준 최근 5일 (평일만)
        today = datetime.today()
        days_checked = 0
        target_days = 5

        while len(results) < target_days and days_checked < 10:  # 최대 10일간 검사 (주말 포함 가능성 때문에)
            date_str = today.strftime("%Y%m%d")
            params = {
                "authkey": EXCHANGE_RATE_API_KEY,
                "searchdate": date_str,
                "data": "AP01"
            }

            response = requests.get(base_url, params=params, verify=certifi.where())
            if response.status_code == 200:
                data = response.json()
                usd_item = next((item for item in data if item.get("cur_unit") == "USD" and item.get("deal_bas_r")), None)
                if usd_item:
                    results.append({
                        "date": date_str,
                        "data": [usd_item]
                    })

            today -= timedelta(days=1)
            days_checked += 1

        if results:
            return Response(results)
        else:
            return Response({"error": "환율 데이터를 불러올 수 없습니다."}, status=500)