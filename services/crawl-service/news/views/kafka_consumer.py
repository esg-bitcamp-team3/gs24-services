import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crawl_service.settings")
django.setup()

from kafka import KafkaConsumer
import json
from news.tasks import esg_predict_task

consumer = KafkaConsumer(
    'esg_crawl_topic',
    bootstrap_servers='kafka:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='esg_crawler_group',
    session_timeout_ms=30000,
    heartbeat_interval_ms=10000,
)

print("[Kafka Consumer Worker] 실행 대기 중...")

for message in consumer:
    try:
        company_name = message.value["company_name"]
        today_date = message.value.get("date")
        esg_predict_task.delay(company_name, today_date)
        print(f"[Kafka] 작업 등록: {company_name} {today_date}")
    except Exception as e:
        print(f"[Kafka Worker Error] {e}")