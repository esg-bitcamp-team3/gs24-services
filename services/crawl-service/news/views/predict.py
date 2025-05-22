from datetime import datetime
import os

import redis
from rest_framework.views import APIView
from rest_framework.response import Response
import json

from pymongo import MongoClient
from kafka import KafkaProducer
import certifi
# MongoDB 연결
try:
    print("MongoDB 연결 시도")
    client = MongoClient("mongodb+srv://jinpang97:MONGOsj!0122@cluster0.bxnwcsi.mongodb.net/ESG?retryWrites=true&w=majority", tlsCAFile=certifi.where())
    # client = MongoClient("mongodb://mongo:27017/")
    db = client["ESG"]
    collection = db["predictRatings"]
    print("MongoDB 연결 성공")
except Exception as e:
    print(f"MongoDB 연결 실패: {e}")


producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
class PredictESTRatingsView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0, decode_responses=True)

    def get(self, request):
        try:
            company_name = request.query_params.get('company_name')
            if not company_name:
                return Response({"error": "company_name parameter is required"}, status=400)

            # find
            today_date = datetime.today().strftime('%Y-%m-%d')
            existing = collection.find_one({"company_name": company_name, "date": today_date})
            if existing:
                existing["_id"] = str(existing["_id"])
                return Response(existing, status=200)

            # if not updated, then
            # check if it is processing
            cached = self.redis_client.get(company_name)
            if cached:
                data = json.loads(cached)
                if data.get("status") == "processing":
                    return Response({"message": "Prediction is processing. Please try again later."}, status=202)
                elif data.get("status") == "done":
                    result = collection.find_one({"company_name": company_name})
                    return Response({"result": result}, status=200)


            # if not
            # set redis and start to process
            self.redis_client.set(company_name, json.dumps({"status": "processing"}), ex=36000)

            msg = {"company_name": company_name, "date": today_date}
            producer.send('esg_crawl_topic', msg)
            producer.flush()
            return Response({"message": "작업이 등록되었습니다. 잠시 후 결과를 조회하세요."}, status=202)

        except Exception as e:
            print(f"API 에러 발생: {e}")
            return Response({"error": str(e)}, status=500)
