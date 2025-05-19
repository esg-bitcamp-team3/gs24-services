from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import time
import random
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime
import json

from pymongo import MongoClient
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import pandas as pd
import re

# MongoDB 연결
try:
    print("🔌 MongoDB 연결 시도")
    client = MongoClient("mongodb+srv://jinpang97:MONGOsj!0122@cluster0.bxnwcsi.mongodb.net/ESG?retryWrites=true&w=majority")
    db = client["ESG"]
    collection = db["preprocessing"]
    print("✅ MongoDB 연결 성공")
except Exception as e:
    print(f"❌ MongoDB 연결 실패: {e}")

# 키워드 불러오기
try:
    print("📄 키워드 파일 로딩 시도")
    keyword_df = pd.read_excel("/app/esg_keywords.xlsx")
    e_keywords = set(keyword_df['Environmental'].dropna().str.replace(" ", "").str.lower())
    s_keywords = set(keyword_df['Social'].dropna().str.replace(" ", "").str.lower())
    g_keywords = set(keyword_df['Governance'].dropna().str.replace(" ", "").str.lower())
    print("✅ 키워드 로딩 성공")
except Exception as e:
    print(f"❌ 키워드 파일 로딩 실패: {e}")

# 모델 로딩
print("🤖 KoELECTRA 모델 로드 시작")
model_name = "monologg/koelectra-base-finetuned-nsmc"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print("✅ 모델 로드 완료")

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
    print("🧪 전처리 및 저장 시작")
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
                collection.insert_one(doc)
            print(f"✅ 저장 완료: {title[:30]}...")

        except Exception as e:
            print(f"❌ 저장 중 에러 발생: {e}")

# 크롬 옵션 설정
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('User-Agent=Mozilla/5.0 ...')
service = Service('/usr/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

class CompanyNewsView(APIView):
    def get(self, request):
        try:
            company_name = request.query_params.get('company_name')
            if not company_name:
                return Response({"error": "company_name parameter is required"}, status=400)

            print(f"📥 요청 받음: {company_name}")
            search_url = f"https://search.naver.com/search.naver?query={company_name}&where=news&pd=3&ds=2025.05.02&de=2025.05.10"
            driver.get(search_url)
            time.sleep(3)

            for _ in range(2):
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
                time.sleep(random.uniform(2, 4))

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            links = [a['href'] for a in soup.find_all('a', href=True) if 'news.naver.com' in a['href']]
            print(f"🔗 기사 링크 수집 완료: {len(links)}개")

            news_data = []
            for link in links:
                title, content, date = self.get_article_content(link)
                if title and content:
                    news_data.append({"title": title, "content": content, "date": date})

            print("📝 뉴스 데이터 수집 완료")
            process_and_store(news_data, company_name)
            print("✅ 전체 저장 완료")
            return Response({"message": f"{company_name} 뉴스 {len(news_data)}건 저장 완료"}, status=200)

        except Exception as e:
            print(f"🔥 API 에러 발생: {e}")
            return Response({"error": str(e)}, status=500)

    def get_article_content(self, link):
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
            print(f"❌ 기사 파싱 실패: {e}")
            return '', '', ''
