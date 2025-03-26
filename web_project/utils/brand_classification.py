import pandas as pd
import torch
import re
from transformers import AutoTokenizer, AutoModelForSequenceClassification


# 1차 브랜드 분류 함수
apple_keywords = [
    "갤럭시",
    "ios", "m1", "m2", "애플 실리콘",  # 운영체제 & 칩셋
    "페이스 id", "faceid", "페이스 아이디", "페이스아이디", "트루뎁스",  # 보안 & 생체인식
    "icloud", "아이클라우드", "에어드롭", "에어드랍",  # 클라우드 & 공유 기능
    "맥세이프", "magsafe", "다이나믹 아일랜드",  # 디스플레이 & 디자인
    "애플페이", "애플 페이", "애플 월렛",  # 결제 & 서비스
    "시리", "siri", "뉴럴 엔진",  # 음성 & AI
    "애플케어",  # 보증 & 지원
    "애플 뮤직",  # 음악 & 미디어
    "라이트닝"  # 기타
]

samsung_keywords = [
    "아이폰",
    "안드로이드", "엑시노스", "액시노스", "스냅드래곤",  # 운영체제 & 칩셋
    "초음파",  # 보안 & 생체인식
    "아몰레드", "amoled", "고릴라 글래스", "폴더블", "폴더블폰",  # 디스플레이 & 디자인
    "s펜", "spen", "s pen",  # 입력 도구
    "삼성 페이", "삼페", "삼성페이", "삼성 월렛",  # 결제 & 서비스
    "빅스비",  # 음성 & AI
    "삼성 헬스",  # 건강 & 웨어러블
    "방수방진", "빅터스",  # 보안 & 내구성
    "dex",  # 생산성 & 확장성
    "굿락", "good lock",  # 커스터마이징 & 편의 기능
    "s시리즈", "갤럭시", "겔럭시", "삼성"  # 기타
]

def has_brand_keyword(comment):
    return any(keyword in comment for keyword in apple_keywords + samsung_keywords)

# 2차 브랜드 분류 모델 불러오기
model_path = "/home/lab12/brand_classification_model.pth"  
model_name = "beomi/KcELECTRA-base-v2022"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=3)

# 가중치 로드
model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))

# GPU/CPU 할당
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# 모델을 평가 모드로 변경
model.eval()

# 브랜드 라벨 매핑
label_map = {0: "samsung", 1: "apple", 2: "none"}

def predict_brand(text):
    """
    저장된 모델을 사용하여 브랜드 2차 분류
    """
    encoding = tokenizer(
        text,
        padding="max_length",
        truncation=True,
        max_length=128,
        return_tensors="pt"
    )

    input_ids = encoding["input_ids"].to(device)
    attention_mask = encoding["attention_mask"].to(device)

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        prediction = torch.argmax(outputs.logits, dim=1).item()

    return label_map[prediction]
