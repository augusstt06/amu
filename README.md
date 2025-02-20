# amu

## 📌 Overview

Flutter + Python을 사용한 AI 맛집 추천 앱입니다.

- 네이버 지도 API를 활용한 맛집 검색
- AI를 통한 리뷰 분석 및 평점 조작 탐지를 실시하고, 최근 등록된 리뷰, 예약 등을 분석해 인기가 급상승한 식당 추천.

## 📌 Skills

### Frontend

<div style="display: flex; gap: 10px;">
<img src="https://img.shields.io/badge/Flutter-02569B?style=for-the-badge&logo=flutter&logoColor=#02569B">
<img src="https://img.shields.io/badge/Dart-0175C2?style=for-the-badge&logo=dart&logoColor=#0175C2">
</div>

### Backend

<div style="display: flex; gap: 10px;">
<img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=flutter&logoColor=##3776AB">
<img src="https://img.shields.io/badge/fastapi-009688?style=for-the-badge&logo=dart&logoColor=##009688">
</div>

### AI 모델

KoBERT, Scikit-learn

## 📌 Launch

### Frontend

```zsh
cd frontend

flutter pub get
```

### Backend

```zsh
cd backend

# 가상환경 설치
python3.12 -m venv venv

# mac
source venv/bin/activate
# window
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn main:app --reload

# 가상환경 종료
deactivate
```
