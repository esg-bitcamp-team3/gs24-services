import json
import time

import redis
import requests
import os

from finance_service import settings

INVEST_APP_KEY = settings.INVEST_APP_KEY
INVEST_SECRET_KEY = settings.INVEST_SECRET_KEY

TOKEN_REDIS_KEY = "koreainvestment_access_token"

class InvestmentViewMixin:
    def __init__(self):
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0, decode_responses=True)
        self.invest_app_key = INVEST_APP_KEY
        self.invest_secret_key = INVEST_SECRET_KEY

    def get_access_token(self):
        token_data = self.redis_client.get(TOKEN_REDIS_KEY)
        if token_data:
            token_info = json.loads(token_data)
            expires_at = token_info.get("expires_at", 0)
            now = time.time()
            if expires_at - now > 300:
                return token_info["access_token"]

        url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
        }
        payload = {
            "grant_type": "client_credentials",
            "appkey": INVEST_APP_KEY,
            "appsecret": INVEST_SECRET_KEY,
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            expires_in = data.get("expires_in", 86400)

            if access_token:
                now = time.time()
                token_info = {
                    "access_token": access_token,
                    "expires_at": now + expires_in
                }
                self.redis_client.set(TOKEN_REDIS_KEY, json.dumps(token_info), ex=expires_in)
                return access_token
            else:
                raise Exception("access_token이 응답에 없습니다.")
        else:
            print(response)
            raise Exception(f"토큰 요청 실패: {response.status_code} {response.text}")