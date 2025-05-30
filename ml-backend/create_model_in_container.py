import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# 데이터 로드
file = "TPN_ML_OMITTED.xlsx"
df = pd.read_excel(file)

# 특성 및 타겟 분리
X = df[['Glucose(serum)', 'Albumin', 'BUN', 'Phosphorus', 'Total Protein']]
Y = df[['TPNCALCULATEDGLUCOSE', 'TPNCALCULATEDPROTEIN', 'TPNCALCULATEDLIPID', 'TPNCALCULATEDCALORI']]

# 훈련 및 테스트 데이터 분리
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

# 정규화
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 모델 훈련
model = RandomForestRegressor(n_estimators=100, max_depth=11, min_samples_leaf=5, min_samples_split=5, random_state=42)
model.fit(X_train_scaled, Y_train)

# 저장
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

print("모델과 스케일러 생성 완료")