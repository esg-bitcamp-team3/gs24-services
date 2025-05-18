from collections import Counter

from konlpy.tag import Okt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from transformers import ElectraTokenizer, ElectraForSequenceClassification, AutoTokenizer, \
    AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
import requests

from search_service import settings

NAVER_CLIENT_ID = settings.NAVER_CLIENT_ID
NAVER_CLIENT_SECRET = settings.NAVER_CLIENT_SECRET

class SentimentModelMixin:
    MODEL_NAME = "monologg/koelectra-base-finetuned-nsmc"

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL_NAME, num_labels=2)
        self.model.to(self.device)
        self.model.eval()
        self.okt = Okt()

    def get_keywords_from_api(self, query, display, target):
        url = f"https://openapi.naver.com/v1/search/{target}.json?query=\"{query}\"&display={display}&start=1&sort=date"
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return []

        items = response.json().get("items", [])
        return [item.get("description") + item.get("title") for item in items]

class TextSentimentAnalysisView(SentimentModelMixin, APIView):
    def __init__(self, **kwargs):
        super().__init__()

    def count_sentiment_texts(self, texts):
        if not texts:
            return None

        inputs = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=128)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            preds = torch.argmax(F.softmax(outputs.logits, dim=1), dim=1).tolist()

        return {
            "negatives": preds.count(0),
            "positives": preds.count(1),
        }

    def get(self, request):
        query = request.GET.get('query', "")
        display = int(request.GET.get('display', 30))

        if not query:
            return Response({"error": "query 파라미터가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        all_texts = []
        for target in ["news", "cafearticle", "blog"]:
            all_texts.extend(self.get_keywords_from_api(query, display, target))

        result = self.count_sentiment_texts(all_texts)
        return Response({"result": result})


class KeywordSentimentAnalysisView(SentimentModelMixin, APIView):
    def __init__(self, **kwargs):
        super().__init__()

    def analyze_keywords_by_sentiment(self, texts):
        if not texts:
            return {"positive_keywords": [], "negative_keywords": []}

        inputs = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=128)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = F.softmax(outputs.logits, dim=1)
            preds = torch.argmax(probs, dim=1).tolist()

        # 단어 감정 통계 카운터
        pos_counter = Counter()
        neg_counter = Counter()

        for text, pred in zip(texts, preds):
            nouns = [n for n in self.okt.nouns(text) if len(n) > 1]
            if pred == 1:
                pos_counter.update(nouns)
            else:
                neg_counter.update(nouns)

        all_keywords = set(pos_counter.keys()).union(set(neg_counter.keys()))
        positive_keywords = []
        negative_keywords = []

        for word in all_keywords:
            pos_count = pos_counter[word]
            neg_count = neg_counter[word]

            if pos_count + neg_count < 2:
                continue

            if pos_count > neg_count:
                positive_keywords.append((word, pos_count))
            else:
                negative_keywords.append((word, neg_count))

        positive_keywords = [w for w, _ in sorted(positive_keywords, key=lambda x: -x[1])[:20]]
        negative_keywords = [w for w, _ in sorted(negative_keywords, key=lambda x: -x[1])[:20]]

        return {
            "positive_keywords": positive_keywords,
            "negative_keywords": negative_keywords,
        }

    def get(self, request):
        query = request.GET.get('query', "")
        display = int(request.GET.get('display', 10))

        if not query:
            return Response({"error": "query 파라미터가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        all_texts = []
        for target in ["news", "cafearticle", "blog"]:
            all_texts.extend(self.get_keywords_from_api(query, display, target))

        keyword_result = self.analyze_keywords_by_sentiment(all_texts)

        return Response({
            "positive_keywords": keyword_result["positive_keywords"],
            "negative_keywords": keyword_result["negative_keywords"],
        })