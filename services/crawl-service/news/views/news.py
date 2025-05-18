from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import random
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime
import json

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

driver = webdriver.Chrome(options=chrome_options)

class CompanyNewsView(APIView):
    def get(self, request):
        company_name = request.query_params.get('company_name')
        if not company_name:
            return Response({"error": "company_name parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        search_url = f"https://search.naver.com/search.naver?ssc=tab.news.all&query={company_name}&sm=tab_opt&sort=0&photo=0&field=0&pd=-1&ds=2025.05.02&de=2025.05.02&docid=&related=0&mynews=1&office_type=1&office_section_code=1&news_office_checked=&nso=&is_sug_officeid=0&office_category=0&service_area="

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
