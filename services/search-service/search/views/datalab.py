from collections import Counter

import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from search_service import settings

NAVER_CLIENT_ID = settings.NAVER_CLIENT_ID
NAVER_CLIENT_SECRET = settings.NAVER_CLIENT_SECRET

class DatalabKeywordView(APIView):
    def get(self, request):
        query = request.GET.get('query', "")
        keywords = request.GET.get('keywords', "")
        start_date = request.GET.get('start_date', "2025-01-01")
        end_date = request.GET.get('end_date', "2025-04-30")
        time_unit = request.GET.get('time_unit', "month")

        if not keywords:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        url = f"https://openapi.naver.com/v1/datalab/search"

        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }

        keyword_groups = []
        for kw in keywords.split(","):
            kw = kw.strip()
            group = {
                "groupName": kw,
                "keywords": [kw, query]
            }
            keyword_groups.append(group)

        body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "keywordGroups": keyword_groups,
        }

        response = requests.post(url, headers=headers, json=body)

        if response.status_code == 200:
            data = response.json()
            results = data["results"]

            return Response(results, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to fetch data from Naver API"}, status=500)

