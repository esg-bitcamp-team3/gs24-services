import os, sys

# ───────────────────────────────────────────────────────────────
# 1) Make sure /app is on Python’s import path so that
#    Python can find preprocessing_service/
HERE = os.path.dirname(__file__)                  # …/news/views
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))  # /app
sys.path.insert(0, ROOT)
# ───────────────────────────────────────────────────────────────

import torch
from datetime import datetime
from pymongo import MongoClient
from django.conf import settings

# 1) 모델 클래스 import
from preprocessing_service.pytorch_e import ESG_CNN       # :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}

# 2) 디바이스 설정
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 3) 가중치 파일 경로
WEIGHT_DIR = os.path.join(
    settings.BASE_DIR,
    "services",
    "preprocessing_service"
)

MODEL_CONFIG = {
    "E": {
        "cls": ESG_CNN,
        "weight": os.path.join(WEIGHT_DIR, "E_predictor.pth"),
        "field": "e_score"
    },
    "S": {
        "cls": ESG_CNN,
        "weight": os.path.join(WEIGHT_DIR, "S_predictor.pth"),
        "field": "s_score"
    },
    "G": {
        "cls": ESG_CNN,
        "weight": os.path.join(WEIGHT_DIR, "G_predictor.pth"),
        "field": "g_score"
    }
}

# 4) 모델 로드
loaded_models = {}
for cat, cfg in MODEL_CONFIG.items():
    m = cfg["cls"]().to(device)
    m.load_state_dict(torch.load(cfg["weight"], map_location=device))
    m.eval()
    loaded_models[cat] = m

# 5) MongoDB 연결 (소스와 타깃이 같다면 하나만)
client     = MongoClient(settings.MONGO_SRC_URI)
src_coll   = client[settings.MONGO_SRC_DB][settings.MONGO_SRC_COLL]
tgt_client = MongoClient(settings.MONGO_TGT_URI)
tgt_coll   = tgt_client[settings.MONGO_TGT_DB][settings.MONGO_TGT_COLL]


def compute_monthly_features(docs):
    # (이전과 동일한 월별 평균 피처 계산 함수)
    features = []
    for month in range(1, 13):
        bucket = [
            d for d in docs
            if datetime.strptime(d["date"], "%Y-%m-%d").month == month
        ]
        if bucket:
            avg_t = sum(d["title_sentiment"]   for d in bucket) / len(bucket)
            avg_c = sum(d["content_sentiment"] for d in bucket) / len(bucket)
            features.append([avg_t, avg_c])
        else:
            features.append([0.0, 0.0])
    return features


def run_all_predictions():
    companies = src_coll.distinct("company_name")
    for comp in companies:
        for cat, cfg in MODEL_CONFIG.items():
            # 6) 카테고리별로 필터링
            docs = list(src_coll.find({
                "company_name": comp,
                "category":      cat  # E, S, G 로 구분된 필드가 있어야 합니다
            }))
            if not docs:
                continue

            # 7) 피처 생성 → 텐서 변환
            feats = compute_monthly_features(docs)
            x = (
                torch.tensor(feats, dtype=torch.float32)
                     .view(1, 12, 2)
                     .to(device)
            )

            # 8) 예측
            with torch.no_grad():
                logits = loaded_models[cat](x)
                pred   = torch.argmax(logits, dim=1).item() + 1

            # 9) 결과 저장
            tgt_coll.update_one(
                {"company_name": comp},
                {
                    "$set": {
                        cfg["field"]:       pred,
                        f"{cfg['field']}_at": datetime.utcnow()
                    }
                },
                upsert=True
            )

            print(f"[{cat}-PREDICT] {comp} → {cfg['field']}={pred}")


if __name__ == "__main__":
    run_all_predictions()
