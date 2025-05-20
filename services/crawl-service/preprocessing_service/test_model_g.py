import torch
import pandas as pd
from pytorch_g import ESG_CNN

E_weight = "./E_predictor.pth"
S_weight = "./S_predictor.pth"
G_weight = "./G_predictor.pth"

company_name = ""
file = pd.read_csv(f"./filtered_test/{company_name}_g.csv")
df = pd.DataFrame(file)

x_input = []
data_1 = []
data_2 = []
data_3 = []
data_4 = []
data_5 = []
data_6 = []
data_7 = []
data_8 = []
data_9 = []
data_10 = []
data_11 = []
data_12 = []

for idx in range(len(df)):
    row = df.iloc[idx]
    month = int(row["date"].split("-")[1])  # Extract month from "YYYY-mm-dd"
    match month:
        case 1:
            data_1.append(row)
        case 2:
            data_2.append(row)
        case 3:
            data_3.append(row)
        case 4:
            data_4.append(row)
        case 5:
            data_5.append(row)
        case 6:
            data_6.append(row)
        case 7:
            data_7.append(row)
        case 8:
            data_8.append(row)
        case 9:
            data_9.append(row)
        case 10:
            data_10.append(row)
        case 11:
            data_11.append(row)
        case 12:
            data_12.append(row)

monthly_data = [data_1, data_2, data_3, data_4, data_5, data_6, data_7, data_8, data_9, data_10, data_11, data_12]
print(monthly_data)
for month_data in monthly_data:
    if month_data:  # Check if the list is not empty
        avg_title_sentiment = sum(row["title_sentiment"] for row in month_data) / len(month_data)
        avg_content_sentiment = sum(row["content_sentiment"] for row in month_data) / len(month_data)
        monthly_avg_x = [avg_title_sentiment, avg_content_sentiment]
        print(f"Monthly Average - Title Sentiment: {avg_title_sentiment}, Content Sentiment: {avg_content_sentiment}")
        x_input.append(monthly_avg_x)
    else:
        x_input.append([0, 0])


print("++++++++++++++++++++데이터 전처리 완료했습니다.+++++++++++++++++++++++")


print(x_input)

model = ESG_CNN()
# 학습된 가중치 불러오기
model.load_state_dict(torch.load(G_weight, map_location=torch.device("cpu"), weights_only=True))
model.eval()
# 모델을 평가 모드로 전환

# 전체 데이터를 x_tensor로 변환
x_input = torch.tensor(x_input, dtype=torch.float32)
print(x_input)
x_input = x_input.view(-1, 12, 2)  # [batch_size, 12, 2]

print(x_input)
print(x_input.shape)


with torch.no_grad():
    # 모델 예측
    output = model(x_input)  # 한 번에 전체 데이터 처리

    # 예측 결과로부터 등급 계산
    # grade = torch.round(pred)  # 0~1 → 1~6 등급
    grade = (torch.argmax(output, dim=1) + 1).cpu().numpy()
    print("output:", output)
    print("output:", grade)  # 예측 결과 출력
