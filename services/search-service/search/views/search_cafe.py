from collections import Counter

import requests
from konlpy.tag import Okt
from rest_framework.response import Response
from rest_framework.views import APIView

from search_service import settings

NAVER_CLIENT_ID = settings.NAVER_CLIENT_ID
NAVER_CLIENT_SECRET = settings.NAVER_CLIENT_SECRET

class SearchCafeView(APIView):
    def get(self, request):
        query = request.GET.get('query', "")
        display = request.GET.get('display', 100)

        url = f"https://openapi.naver.com/v1/search/cafearticle.json?query={query}&display={display}&start=1&sort=sim"

        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            blogs = data['items']

            word_cloud_data = self.extract_keywords(blogs)

            return Response(word_cloud_data)
        else:
            return Response({"error": "Failed to fetch data from Naver API"}, status=500)

    def extract_keywords(self, blogs):
        okt = Okt()
        keywords = []

        for blog in blogs:
            description = blog['description'] + blog['title']

            nouns = okt.nouns(description)

            for noun in nouns:
                if len(noun) > 1:
                    keywords.append(noun)

        word_freq = Counter(keywords)

        word_cloud_data = [{"text": word, "value": freq} for word, freq in word_freq.most_common(10)]

        return word_cloud_data
