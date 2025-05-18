from json import dumps

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

import requests
import ssl

from market_service import settings

MARKET_PRICE_API_SERVICE_KEY = settings.MARKET_PRICE_API_SERVICE_KEY

class CarbonPriceView(APIView):
    def get(self, request):
        basDt = request.query_params.get('basDt')
        beginBasDt = request.query_params.get('beginBasDt')
        isinCd = request.query_params.get('isinCd')
        itmsNm = request.query_params.get('itmsNm')
        likeItmsNm = request.query_params.get('likeItmsNm')

        url = "http://apis.data.go.kr/1160100/service/GetGeneralProductInfoService/getCertifiedEmissionReductionPriceInfo"

        params = {
            "serviceKey": MARKET_PRICE_API_SERVICE_KEY,
            "resultType": "json",
        }

        if basDt:
            params["basDt"] = basDt
        if beginBasDt:
            params["beginBasDt"] = beginBasDt
        if isinCd:
            params["isinCd"] = isinCd
        if itmsNm:
            params["itmsNm"] = itmsNm
        if likeItmsNm:
            params["likeItmsNm"] = likeItmsNm

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()

            items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

            return Response(items, status=status.HTTP_200_OK)

        return Response({"error": "Failed to fetch data from API"}, status=500)