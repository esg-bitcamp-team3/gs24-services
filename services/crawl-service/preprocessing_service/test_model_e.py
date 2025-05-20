# test_model_e_mongo.py

import os
import torch
from datetime import datetime
from pymongo import MongoClient

# 1) 모델 클래스 import (경로는 실제 위치에 맞게 조정)
from preprocessing_service.pytorch_e import ESG_CNN

# 2) MongoDB 설정
MONGO_URI  = "mongodb+srv://jinpang97:MONGOsj!0122@cluster0.bxnwcsi.mongodb.net/ESG?retryWrites=true&w=majority"
MONGO_DB   = "ESG"
MONGO_COLL = "preprocessing"

# 3) MongoDB 연결
client     = MongoClient(MONGO_URI)
collection = client[MONGO_DB][MONGO_COLL]

# 4) 월별 평균 피처 계산 함수
def compute_monthly_features(docs):
    """
    docs: list of dicts, 각 dict에 'date' (YYYY-MM-DD),
          'title_sentiment', 'content_sentiment' 필드가 있다고 가정
    returns: List[List[float, float]] 길이 12 (월별)
    """
    # 날짜 파싱해서 datetime 리스트로 변환
    parsed = [
        {
            "date": datetime.strptime(d["date"], "%Y-%m-%d"),
            "title_sentiment": d["title_sentiment"],
            "content_sentiment": d["content_sentiment"]
        }
        for d in docs
    ]

    features = []
    for month in range(1, 13):
        # 해당 월의 docs만 모아서
        bucket = [d for d in parsed if d["date"].month == month]
        if bucket:
            avg_t = sum(d["title_sentiment"] for d in bucket) / len(bucket)
            avg_c = sum(d["content_sentiment"] for d in bucket) / len(bucket)
            features.append([avg_t, avg_c])
        else:
            features.append([0.0, 0.0])
    return features


def main():
    # 5) 예측할 회사 이름 설정
    company_name = "한화"

    # 6) MongoDB 에서 해당 회사 전처리 데이터 가져오기
    docs = list(collection.find({"company_name": company_name}))

    if not docs:
        print(f"[ERROR] '{company_name}' 데이터가 없습니다.")
        return

    # 7) 월별 피처 생성
    monthly_feats = compute_monthly_features(docs)
    x = torch.tensor(monthly_feats, dtype=torch.float32).view(1, 12, 2)

    print("▶ 월별 피처:", monthly_feats)

    # 8) 모델 로드
    E_WEIGHT = "./E_predictor.pth"  # 로컬 혹은 절대 경로
    device   = torch.device("cpu")  # 테스트는 CPU로
    model    = ESG_CNN().to(device)
    model.load_state_dict(torch.load(E_WEIGHT, map_location=device))
    model.eval()

    # 9) 예측
    with torch.no_grad():
        logits = model(x)
        grade  = (torch.argmax(logits, dim=1).item() + 1)

    print(f"💡 {company_name} E-grade 예측값: {grade}")


if __name__ == "__main__":
    main()
