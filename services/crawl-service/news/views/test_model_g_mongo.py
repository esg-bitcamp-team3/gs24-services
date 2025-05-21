import torch
from datetime import datetime, date
from pymongo import MongoClient
from model import ESG_CNN  # 불러온 모델 정의

# DB 설정
MONGO_URI  = "mongodb+srv://jinpang97:MONGOsj!0122@cluster0.bxnwcsi.mongodb.net/ESG?retryWrites=true&w=majority"
client     = MongoClient(MONGO_URI)
docs       = list(client["ESG"]["preprocessing"].find({"company_name":"인디에프"}))

# 저장 DB 설정
SAVE_MONGO_URI = "mongodb+srv://jinpang97:MONGOsj!0122@cluster0.bxnwcsi.mongodb.net/ESG?retryWrites=true&w=majority"
client_save = MongoClient(SAVE_MONGO_URI)
docs_save = list(client_save["ESG"]["predictRatings"].find({"company_name":"인디에프"}))

#오늘 날짜 저장
today_date = datetime.today().isoformat()

for doc in docs:
    print(doc["date"])

dates = [doc["date"] for doc in docs]

# DB에 저장 함수
def save_result_to_mongo(result):
    try:
        client_save["ESG"]["predictRatings"].insert_one(result)
    except Exception as e:
        print(f"Error saving result to MongoDB: {e}")

# 월별 평균 피처 함수
def compute_monthly_features(docs):
    feats = []
    for m in range(1,13):
        bucket = [d for d in docs if datetime.strptime(d["date"], "%Y-%m-%d").month==m]
        if bucket:
            t = sum(d["title_sentiment"]   for d in bucket)/len(bucket)
            c = sum(d["content_sentiment"] for d in bucket)/len(bucket)
            feats.append([t,c])
        else:
            feats.append([0.0,0.0])
    return feats

# 1) DB에서 불러온 docs → 피처 계산 → x_tensor
monthly = compute_monthly_features(docs)
x_tensor = torch.tensor(monthly, dtype=torch.float32).view(1,12,2)

# 2) 모델 로드
model = ESG_CNN()
model.load_state_dict(torch.load("G_predictor.pth", map_location="cpu"))
model.eval()

# 3) 예측
with torch.no_grad():
    out   = model(x_tensor)
    grade = torch.argmax(out, dim=1).item() + 1
    print("Predicted G-grade:", grade)

result = {
    "company_name" : "인디에프",
    "date"    : today_date,
    "g_score" : grade
}

try:
    client_save["ESG"]["predictRatings"].update_one({"company_name": "인디에프"}, {"$set": result}, upsert=True)
    print(f"✅ 저장 성공")
except Exception as e:
    print(f"❌ 저장 실패: {e}")