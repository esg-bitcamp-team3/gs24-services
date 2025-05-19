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

# MongoDB연결 및 전처리 하는 부분 -------------------------------------------
from pymongo import MongoClient
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import pandas as pd
import re

#MongoDB 연결
client = MongoClient("mongodb+srv://jinpang97:MONGOsj!0122@cluster0.bxnwcsi.mongodb.net/ESG?retryWrites=true&w=majority")
db = client["ESG"]
collection = db["preprocessing"]

#키워드 불러오기
keyword_df = pd.read_excel("/app/esg_keywords.xlsx")
e_keywords = set(keyword_df['Environmental'].dropna().str.replace(" ", "").str.lower())
s_keywords = set(keyword_df['Social'].dropna().str.replace(" ", "").str.lower())
g_keywords = set(keyword_df['Governance'].dropna().str.replace(" ", "").str.lower())

#KoELECTRA 모델 로드
model_name = "monologg/koelectra-base-finetuned-nsmc"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# 문장 나누기
def split_into_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

# 감성 분석
def classify_sentiment(text):
    inputs = tokenizer(text, padding=True, truncation=True, max_length=64, return_tensors='pt')
    inputs = {key: val.to(device) for key, val in inputs.items()}
    with torch.no_grad():
        logits = model(**inputs).logits
        prediction = torch.argmax(logits, dim=1).item()
    return prediction

# 전체 전처리 및 MongoDB 저장
def process_and_store(news_list):
    for article in news_list:
        title = article['title']
        content = article['content']
        date = article['date']
        company = article.get('company', 'Unknown')

        # 문장 분리
        content_sents = split_into_sentences(content)
        title_sents = split_into_sentences(title)

        # 감성 점수
        content_scores = [classify_sentiment(s) for s in (content_sents[:3] + content_sents[-3:] if len(content_sents) >= 4 else content_sents)]
        title_scores = [classify_sentiment(s) for s in title_sents]

        content_avg = sum(content_scores) / len(content_scores) if content_scores else 0
        title_avg = sum(title_scores) / len(title_scores) if title_scores else 0

        # 키워드 기반 분류
        text_combined = (title + content).lower().replace(" ", "")
        categories = []
        if any(k in text_combined for k in e_keywords): categories.append("E")
        if any(k in text_combined for k in s_keywords): categories.append("S")
        if any(k in text_combined for k in g_keywords): categories.append("G")
        if not categories: categories.append("Uncategorized")

        # MongoDB에 저장
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

# ----------------------------------------------------------------------------------------
# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
service = Service('/usr/bin/chromedriver')

driver = webdriver.Chrome(service=service, options=chrome_options)

class CompanyNewsView(APIView):
    def get(self, request):
        company_name = request.query_params.get('company_name')
        if not company_name:
            return Response({"error": "company_name parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        search_url = f"https://search.naver.com/search.naver?query={company_name}&where=news&sm=tab_opt&sort=0&photo=0&field=0&pd=3&ds=2025.05.02&de=2025.05.10"

        driver.get(search_url)
        time.sleep(3)

        for _ in range(2):
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(random.uniform(2, 5))

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        links = []
        for link in soup.find_all('a', href=True):
            if 'news.naver.com' in link['href']:
                links.append(link['href'])

        news_data = []
        for link in links:
            title, content, date = self.get_article_content(link)
            if title and content:
                news_data.append({"title": title, "content": content, "date": date})

        return Response(news_data)
        #전처리 시키고 DB에 저장하기
        # process_and_store(news_data)
        # return Response({
        #     "message": f"{company_name} 관련 뉴스 {len(news_data)}건 크롤링 및 저장 완료",
        #     "saved_count": len(news_data)
        # })
        #--------------------------------------------------------------------

    def get_article_content(self, link):
        driver.get(link)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        title = ''
        try:
            title_tag = soup.find('h2', {'class': 'media_end_head_headline'})
            if title_tag:
                title = title_tag.get_text(strip=True)
        except AttributeError:
            print(f"제목을 찾을 수 없습니다: {link}")

        # 뉴스 본문 추출
        content = ''
        try:
            content_tag = soup.find('article', {'id': 'dic_area'})
            if content_tag:
                content = content_tag.get_text(strip=True)
        except AttributeError:
            print(f"본문을 찾을 수 없습니다: {link}")

        date = ''
        try:
            date_tag = soup.find('span', {'class': 'media_end_head_info_datestamp_time'})
            if date_tag and date_tag.has_attr('data-date-time'):
                date = date_tag['data-date-time']

                date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                date = date_obj.strftime("%Y-%m-%d")
        except AttributeError:
            print(f"발행일자를 찾을 수 없습니다: {link}")

        return title, content, date
