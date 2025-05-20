import torch
import torch.nn as nn
import torch.optim as optim
import os
import glob
import pandas as pd
from datetime import datetime
import ast
from torch.utils.data import TensorDataset, DataLoader
import torch.nn.functional as F
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler
from sklearn.metrics import accuracy_score


folder_path = "./filtered"
file_pattern = "*_s.csv"  # 예: 파일 이름에 '.csv'가 포함된 경우

# 파일 경로 리스트 불러오기
csv_files = glob.glob(os.path.join(folder_path, file_pattern))

grade_2022 = pd.read_csv("./company_grades/2022_평가등급(2023).csv", encoding='utf-8-sig', header=0)
grade_2023 = pd.read_csv("./company_grades/2023_평가등급(2024).csv", encoding='utf-8-sig', header=0)
grade_2024 = pd.read_csv("./company_grades/2024_평가등급(2025).csv", encoding='utf-8-sig', header=0)


# ESG_greade to number
ESG_grade = [
    {"A+": 6},
    {"A": 5},
    {"B+": 4},
    {"B": 3},
    {"C": 2},
    {"D": 1},
    {"등급없음": 0}]

def main():
  all_x = []
  all_y = []
  for file in csv_files:
    try:
        file_name = os.path.basename(file)[:-6]
        df = pd.read_csv(file, encoding='utf-8-sig', header=0)
        
        # 데이터가 없는 경우 (헤더만 존재)
        if df.empty:
            print(f"헤더만 있고 데이터가 없어 건너뜀: {file}")
            continue

    except pd.errors.EmptyDataError:
        print(f"파일이 완전히 비어 있어 건너뜀: {file}")
        continue
    
    matching_rows_2022 = grade_2022[grade_2022["기업명"] == file_name]
    matching_rows_2023 = grade_2023[grade_2023["기업명"] == file_name]
    matching_rows_2024 = grade_2024[grade_2024["기업명"] == file_name]

    ESG_grade_2022 = matching_rows_2022["사회"].map(lambda grade: next((value for d in ESG_grade for key, value in d.items() if key == grade), 0))
    ESG_grade_2023 = matching_rows_2023["사회"].map(lambda grade: next((value for d in ESG_grade for key, value in d.items() if key == grade), 0))
    ESG_grade_2024 = matching_rows_2024["사회"].map(lambda grade: next((value for d in ESG_grade for key, value in d.items() if key == grade), 0))

    data_2022 = df[df["date"].str.startswith("2022")]
    data_2023 = df[df["date"].str.startswith("2023")]
    data_2024 = df[df["date"].str.startswith("2024")]

    if not data_2022.empty:
        for idx in range(len(data_2022)):
          row = data_2022.iloc[idx]
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
        yealy_avg_x = []
        for month_data in monthly_data:
          if month_data:  # Check if the list is not empty
            avg_title_sentiment = sum(row["title_sentiment"] for row in month_data) / len(month_data)
            avg_content_sentiment = sum(row["content_sentiment"] for row in month_data) / len(month_data)
            monthly_avg_x = [avg_title_sentiment, avg_content_sentiment]
            yealy_avg_x.append(monthly_avg_x)
            print(f"Monthly Average - Title Sentiment: {avg_title_sentiment}, Content Sentiment: {avg_content_sentiment}")
          else:
             monthly_avg_x = [0, 0]
        if ESG_grade_2022.values != 0:
          all_x.append(yealy_avg_x)
          all_y.append(ESG_grade_2022)

    if not data_2023.empty:
        for idx in range(len(data_2023)):
          row = data_2023.iloc[idx]
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
        yealy_avg_x = []
        for month_data in monthly_data:
          if month_data:  # Check if the list is not empty
            avg_title_sentiment = sum(row["title_sentiment"] for row in month_data) / len(month_data)
            avg_content_sentiment = sum(row["content_sentiment"] for row in month_data) / len(month_data)
            monthly_avg_x = [avg_title_sentiment, avg_content_sentiment]
            yealy_avg_x.append(monthly_avg_x)
            print(f"Monthly Average - Title Sentiment: {avg_title_sentiment}, Content Sentiment: {avg_content_sentiment}")
          else:
            monthly_avg_x = [0, 0]
        if ESG_grade_2023.values != 0:
          all_x.append(yealy_avg_x)
          all_y.append(ESG_grade_2023)
    
    if not data_2024.empty:
        for idx in range(len(data_2024)):
          row = data_2024.iloc[idx]
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
        yealy_avg_x = []
        for month_data in monthly_data:
          print(month_data)
          if month_data:  # Check if the list is not empty
            avg_title_sentiment = sum(row["title_sentiment"] for row in month_data) / len(month_data)
            avg_content_sentiment = sum(row["content_sentiment"] for row in month_data) / len(month_data)
            monthly_avg_x = [avg_title_sentiment, avg_content_sentiment]
            yealy_avg_x.append(monthly_avg_x)
            print(f"Monthly Average - Title Sentiment: {avg_title_sentiment}, Content Sentiment: {avg_content_sentiment}")
          else:
             monthly_avg_x = [0, 0]
        if ESG_grade_2024.values != 0:
          all_x.append(yealy_avg_x)
          all_y.append(ESG_grade_2024)

    print("++++++++++++++++++++데이터 전처리 중입니다.+++++++++++++++++++++++")


  print("++++++++++++++++++++데이터 전처리 완료했습니다.+++++++++++++++++++++++")

  all_y = [float(y.values[0]) for y in all_y]
  x_tensor = torch.tensor(all_x, dtype=torch.float32)  # [12, 2]
  y_tensor = torch.tensor(all_y, dtype=torch.float32).squeeze() # [1, 1]
  y_tensor = (y_tensor-1).long()
  print(y_tensor)
  print(type(y_tensor))
  print(len(x_tensor))
  print(len(y_tensor))
  return x_tensor, y_tensor



class ESG_CNN(nn.Module):
    def __init__(self):
        super(ESG_CNN, self).__init__()

        # 입력: [batch_size, 2, 12]
        self.conv1 = nn.Conv1d(in_channels=2, out_channels=32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(32)
        self.relu1 = nn.ReLU()

        self.conv2 = nn.Conv1d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(64)
        self.relu2 = nn.ReLU()

        self.global_pool = nn.AdaptiveMaxPool1d(1)  # → [batch_size, 64, 1]
        self.fc = nn.Linear(64, 6)  # 회귀값 출력  

    def forward(self, x):
        # x: [batch_size, 12, 2] → Conv1D는 [batch_size, channels, seq_len] 요구
        x = x.permute(0, 2, 1)  # [B, 2, 12]

        x = self.relu1(self.bn1(self.conv1(x)))  # [B, 32, 12]
        x = self.relu2(self.bn2(self.conv2(x)))  # [B, 64, 12]

        x = self.global_pool(x)  # [B, 64, 1]
        x = x.squeeze(-1)        # [B, 64]
        logits = self.fc(x)
        return logits



# 가중치 추가
def compute_class_weights(y_tensor, num_classes):
    label_counts = Counter(y_tensor.tolist())
    total_samples = len(y_tensor)

    # 각 클래스에 대한 weight 계산: 클래스가 적을수록 weight가 큼
    class_weights = {cls: total_samples / (num_classes * count) for cls, count in label_counts.items()}

    # 각 샘플별 weight 리스트 생성
    sample_weights = [class_weights[label.item()] for label in y_tensor]

    # WeightedRandomSampler 생성
    sampler = WeightedRandomSampler(weights=sample_weights, num_samples=len(sample_weights), replacement=True)

    return sampler

# 학습 함수

def train_model(model, x_tensor, y_tensor, epochs=200, batch_size=32):
    sampler = compute_class_weights(y_tensor, num_classes=6)
    # 4) TensorDataset 및 DataLoader 생성 (sampler 적용)
    dataset = TensorDataset(x_tensor, y_tensor)
    loader = DataLoader(dataset, batch_size=batch_size, sampler=sampler)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0

        for inputs, targets in loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * inputs.size(0)

        epoch_loss = running_loss / len(loader.dataset)
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{epochs}], Loss: {epoch_loss:.4f}")

    # 훈련 모델 평가 및 시각화
    model.eval()
    with torch.no_grad():
        outputs = model(x_tensor)
        preds = torch.argmax(outputs, dim=1)
        predictions = (preds + 1).cpu().numpy()
        targets = (y_tensor + 1).cpu().numpy()
        accuracy = accuracy_score(y_tensor.cpu().numpy(), preds.cpu().numpy())
        print(f"Accuracy: {accuracy * 100:.2f}%")


    plt.figure(figsize=(10, 6))
    sns.histplot(targets, label='Actual', kde=True, color='blue', stat='density', bins=30)
    sns.histplot(predictions, label='Predicted', kde=True, color='orange', stat='density', bins=30)
    plt.title("Distribution of Predictions vs Actuals")
    plt.xlabel("Value")
    plt.ylabel("Density")
    plt.legend()
    plt.grid(True)
    plt.show()

    torch.save(model.state_dict(), 'S_predictor.pth')

# 예측 함수
def predict(model_path, x_tensor):
    model = ESG_CNN()
    model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
    model.eval()

    with torch.no_grad():
        output = model(x_tensor)
        grade = int(torch.round(output * 6 + 1))
        print("output:", grade)

# 메인 실행 분기
if __name__ == "__main__":
    mode = "train"  # "train" or "predict"

    if mode == "train":
        X_tensor, Y_tensor = main()
        print(X_tensor)
        print(Y_tensor)
        model = ESG_CNN()
        train_model(model, X_tensor, Y_tensor)

    # elif mode == "predict":
        # predict("E_predictor.pth", x_tensor)