# app/tasks.py
import redis
from celery import shared_task
import time
from pymongo import MongoClient
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import random
import re
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import pandas as pd

from news.views.model import ESG_CNN
import certifi
import json

redis_client = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)

try:
    print("MongoDB 연결 시도")
    client = MongoClient("mongodb+srv://jinpang97:MONGOsj!0122@cluster0.bxnwcsi.mongodb.net/ESG?retryWrites=true&w=majority", tlsCAFile=certifi.where())
    # client = MongoClient("mongodb://mongo:27017/")
    db = client["ESG"]
    preprecessing = db["preprocessing"]
    predictRating = db["predictRatings"]
    print("MongoDB 연결 성공")
except Exception as e:
    print(f"MongoDB 연결 실패: {e}")


# 키워드 불러오기 (한번만 로딩되도록 모듈 레벨에)
keyword_df = pd.read_excel("/app/esg_keywords.xlsx")
e_keywords = set(keyword_df['Environmental'].dropna().str.replace(" ", "").str.lower())
s_keywords = set(keyword_df['Social'].dropna().str.replace(" ", "").str.lower())
g_keywords = set(keyword_df['Governance'].dropna().str.replace(" ", "").str.lower())

# 모델 로딩 (한번만)
model_name = "monologg/koelectra-base-finetuned-nsmc"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def split_into_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

def classify_sentiment(text):
    inputs = tokenizer(text, padding=True, truncation=True, max_length=64, return_tensors='pt')
    inputs = {key: val.to(device) for key, val in inputs.items()}
    with torch.no_grad():
        logits = model(**inputs).logits
        prediction = torch.argmax(logits, dim=1).item()
    return prediction

def process_and_store(news_list, company_name):
    for article in news_list:
        try:
            title = article['title']
            content = article['content']
            date = article['date']
            company = article.get('company', company_name)

            content_sents = split_into_sentences(content)
            title_sents = split_into_sentences(title)

            content_scores = [classify_sentiment(s) for s in (content_sents[:3] + content_sents[-3:] if len(content_sents) >= 4 else content_sents)]
            title_scores = [classify_sentiment(s) for s in title_sents]

            content_avg = sum(content_scores) / len(content_scores) if content_scores else 0
            title_avg = sum(title_scores) / len(title_scores) if title_scores else 0

            text_combined = (title + content).lower().replace(" ", "")
            categories = []
            if any(k in text_combined for k in e_keywords): categories.append("E")
            if any(k in text_combined for k in s_keywords): categories.append("S")
            if any(k in text_combined for k in g_keywords): categories.append("G")
            if not categories: categories.append("Uncategorized")

            for cat in categories:
                doc = {
                    "company": company,
                    "title": title,
                    "content": content,
                    "date": date,
                    "title_sentiment": title_avg,
                    "content_sentiment": content_avg,
                    "category": cat
                }
                preprecessing.insert_one(doc)

        except Exception as e:
            print(f"저장 중 에러 발생: {e}")

def crawl_and_process_news(company_name):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('User-Agent=Mozilla/5.0 ...')
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)

    today = datetime.today()
    # 이번 달 1일
    start_date = today.replace(day=1).strftime('%Y.%m.%d')
    # 오늘
    end_date = today.strftime('%Y.%m.%d')

    try:
        search_url = f"https://search.naver.com/search.naver?query={company_name}&where=news&pd=3&ds={start_date}&de={end_date}"
        driver.get(search_url)
        time.sleep(3)

        for _ in range(2):
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(random.uniform(2, 4))

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True) if 'news.naver.com' in a['href']]

        news_data = []
        for link in links:
            title, content, date = get_article_content(driver, link)
            if title and content:
                news_data.append({"title": title, "content": content, "date": date})

        process_and_store(news_data, company_name)

    finally:
        driver.quit()

def get_article_content(driver, link):
    try:
        driver.get(link)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        title_tag = soup.find('h2', {'class': 'media_end_head_headline'})
        title = title_tag.get_text(strip=True) if title_tag else ''

        content_tag = soup.find('article', {'id': 'dic_area'})
        content = content_tag.get_text(strip=True) if content_tag else ''

        date_tag = soup.find('span', {'class': 'media_end_head_info_datestamp_time'})
        if date_tag and date_tag.has_attr('data-date-time'):
            date = datetime.strptime(date_tag['data-date-time'], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        else:
            date = ''

        return title, content, date
    except Exception as e:
        print(f"기사 파싱 실패: {e}")
        return '', '', ''

def compute_monthly_features(docs):
    feats = []
    for m in range(1, 13):
        bucket = [d for d in docs if d.get("date") and datetime.strptime(d["date"], "%Y-%m-%d").month == m]
        if bucket:
            t = sum(d["title_sentiment"] for d in bucket) / len(bucket)
            c = sum(d["content_sentiment"] for d in bucket) / len(bucket)
            feats.append([t, c])
        else:
            feats.append([0.0, 0.0])
    return feats

@shared_task
def esg_predict_task(company_name, today_date=None):
    print("처리 시작 ===========================")
    if today_date is None:
        today_date = datetime.today().strftime('%Y-%m-%d')

    crawl_and_process_news(company_name)

    print("전처리 완료 ==========================")

    docs = preprecessing.find({
        "company_name": company_name,
        "date": {"$gte": "2025-01-01", "$lte": "2025-12-31"}
    })

    print("전처리 데이터 ==========================")

    docs_e = [d for d in docs if d["category"] == "E"]
    docs_s = [d for d in docs if d["category"] == "S"]
    docs_g = [d for d in docs if d["category"] == "G"]

    def to_features(docs_cat):
        if docs_cat:
            return compute_monthly_features(docs_cat)
        else:
            return [[0.0, 0.0]] * 12

    monthly_e = to_features(docs_e)
    monthly_s = to_features(docs_s)
    monthly_g = to_features(docs_g)

    x_tensor_e = torch.tensor(monthly_e, dtype=torch.float32).view(1, 12, 2)
    x_tensor_s = torch.tensor(monthly_s, dtype=torch.float32).view(1, 12, 2)
    x_tensor_g = torch.tensor(monthly_g, dtype=torch.float32).view(1, 12, 2)

    model_e = ESG_CNN()
    model_e.load_state_dict(torch.load("news/views/E_predictor.pth", map_location="cpu"))
    model_e.eval()
    model_s = ESG_CNN()
    model_s.load_state_dict(torch.load("news/views/S_predictor.pth", map_location="cpu"))
    model_s.eval()
    model_g = ESG_CNN()
    model_g.load_state_dict(torch.load("news/views/G_predictor.pth", map_location="cpu"))
    model_g.eval()

    result = {
        "company_name": company_name,
        "date": today_date
    }

    with torch.no_grad():
        result["e_score"] = torch.argmax(model_e(x_tensor_e), dim=1).item() + 1 if docs_e else None
        result["s_score"] = torch.argmax(model_s(x_tensor_s), dim=1).item() + 1 if docs_s else None
        result["g_score"] = torch.argmax(model_g(x_tensor_g), dim=1).item() + 1 if docs_g else None

    dt = datetime.strptime(today_date, "%Y-%m-%d")
    year_month = dt.strftime("%Y-%m")  # "2025-05"

    # 같은 회사, 같은 연-월 범위 조건 (date가 "2025-05-01" 이상 "2025-05-31" 이하인 문서)
    start_date = f"{year_month}-01"
    end_date = f"{year_month}-31"

    predictRating.update_one(
        {
            "company_name": company_name,
            "date": {"$gte": start_date, "$lte": end_date}
        },
        {"$set": {
            "date": today_date,
            **result
        }},
        upsert=True
    )

    print("업데이트 ======================================")

    status_data = {"status": "done"}
    redis_client.set(company_name, json.dumps(status_data), ex=36000)

    print(f"[완료] {company_name} {today_date} 예측 결과 저장됨")
    return result