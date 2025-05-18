import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from finance_service import settings

CRTFC_KEY = settings.OPEN_DART_API_KEY

class SingleCompanyFinancialAPIView(APIView):
    def get(self, request):
        crtfc_key = CRTFC_KEY
        corp_code = request.GET.get("corp_code")
        bsns_year = request.GET.get("year")
        reprt_code = request.GET.get("report_code")
        fs_div = request.GET.get("fs_div", "OFS")

        if not all([crtfc_key, corp_code, bsns_year, reprt_code, fs_div]):
            return Response(
                {"error": "Missing required query parameters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
        params = {
            "crtfc_key": crtfc_key,
            "corp_code": corp_code,
            "bsns_year": bsns_year,
            "reprt_code": reprt_code,
            "fs_div": fs_div,
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            return Response(data)
        else:
            return Response(
                {"error": "Failed to fetch data from DART API."},
                status=response.status_code,
            )