from rest_framework.views import APIView
from rest_framework.response import Response
from pymongo import MongoClient
from datetime import datetime
from kafka import KafkaProducer
import json

# (Mongo, DB 연결)
client = MongoClient("mongodb+srv://jinpang97:MONGOsj!0122@cluster0.bxnwcsi.mongodb.net/ESG?retryWrites=true&w=majority")
db = client["ESG"]
predictRatings = db["predictRatings"]

# Kafka producer 연결
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

class FinalCompanyNewsView(APIView):
    def get(self, request):
        try:
            company_name = request.query_params.get('company_name')
            if not company_name:
                return Response({"error": "company_name parameter is required"}, status=400)
            today_date = datetime.today().strftime('%Y-%m-%d')
            existing = predictRatings.find_one({"company_name": company_name, "date": today_date})
            if existing:
                existing["_id"] = str(existing["_id"])
                return Response(existing, status=200)
            # 결과 없으면 Kafka로 작업 메시지 전송!
            msg = {"company_name": company_name, "date": today_date}
            producer.send('esg_crawl_topic', msg)
            producer.flush()
            return Response({"message": "작업이 등록되었습니다. 잠시 후 결과를 조회하세요."}, status=202)
        except Exception as e:
            print(f"API 에러 발생: {e}")
            return Response({"error": str(e)}, status=500)
