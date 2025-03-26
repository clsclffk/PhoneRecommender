import pandas as pd
import re
import kss
from konlpy.tag import Okt

def clean_data(df):
    # 중복 제거
    df = df.drop_duplicates()

    # 영어와 공백만 있는 댓글 제거
    df = df[~df["comment"].astype(str).str.fullmatch(r"[a-zA-Z\s]+")]

    # 빈 문자열 혹은 공백만 있는 댓글 제거
    df = df[df["comment"].astype(str).str.strip() != '']

    return df

def clean_text(text, stopwords=None):
    if stopwords is None:
        stopwords = {
            "근데", "진짜", "진쨔", "진짜루", "진짜로", "진쨔루"
        }
    # 원본 저장
    original_text = text

    # 시간 패턴 제거 (예: "12:30" 같은 시간 표현)
    time_pattern = re.compile(r'\b\d{1,2}:\d{2}\b')
    text = time_pattern.sub('', text)
    
    # 특수 문자, 이모지 제거
    text = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', text)
    
    # URL 제거
    url_pattern = re.compile(r'(https?://|www\.)\S+|https\S+|http\S+', re.IGNORECASE)
    text = url_pattern.sub('', text)
    
    # 불필요한 공백 제거
    text = text.strip()
    
    # 자음만 반복되는 경우 제거 (예: ㅋㅋㅋ, ㅎㅎㅎ)
    text = re.sub(r'([ㄱ-ㅎ])\1+', '', text)
    
    # 모음만 반복되는 경우 제거 (예: ㅜㅜㅜ, ㅠㅠㅠ)
    text = re.sub(r'([ㅏ-ㅣ])\1+', '', text)

    # 불용어 제거 (단어 단위로 정확히 제거)
    words = re.findall(r'\b\w+\b', text)  # 단어 단위로 추출

    text = ' '.join([word for word in words if word not in stopwords])

    return text

# 정규화 (브랜드 기종 합치기)
def normalize(text):
    
    # 소문자로 변환
    text = text.lower()
    
    # 삼성 모델 패턴 일반화
    samsung_patterns = [
    r"s\d+\+?",                 # s24, s25+
    r"갤럭시s\d+",              # 갤럭시s24
    r"갤\d+",                   # 갤24
    r"\d+플러스",               # 24플러스
    r"\d+울트라",               # 25울트라
    r"갤\d+울트라",             # 갤25울트라
    r"울트라",                  # 울트라
    r"삼성폰",                  # 삼성폰
    r"갤럭시폰",                # 갤럭시폰
    r"fe",                      # fe
    r"\d+플립",                 # 5플립, 4플립
    r"갤\d+플립",               # 갤5플립
    r"플립",                    # 플립
    r"노트\d+",                 # 노트10, 노트20
    r"갤노트\d+",               # 갤노트10
    r"노트",                    # 노트
    r"\d+폴드",                 # 5폴드, 4폴드
    r"갤\d+폴드",               # 갤5폴드
    r"폴드",                    # 폴드
    r"z폴드"                    # z폴드
]
    
    # 아이폰 모델 패턴 일반화
    iphone_patterns = [
    r"\d{2}pro(max)?",          # 16pro, 16promax
    r"\d{2}프맥",               # 16프맥
    r"프맥\d{2}",               # 프맥15
    r"프맥",                    # 프맥
    r"아이폰\d+",               # 아이폰16
    r"미니",                    # 미니
    r"se",                      # se
    r"pro(max)?",               # pro, promax
    r"프로맥스",                # 프로맥스
    r"프로",                    # 프로
    r"맥스",                     # 맥스
    r"아이폰프로맥스"            # 아이폰프로맥스
]
    
    # 단어가 앞에 나오면 변환 (조사 여부와 관계없이 적용)
    for pattern in samsung_patterns:
        text = re.sub(fr"\b{pattern}", "갤럭시", text)

    for pattern in iphone_patterns:
        text = re.sub(fr"\b{pattern}", "아이폰", text)

    # 불필요한 공백 제거
    text = re.sub(r"\s+", " ", text).strip()
    
    text = text.replace('갤럭시+', '갤럭시')

    return text

# 문장 분리
def split_sentences(text):
    return kss.split_sentences(text)

# 명사 추출
def extract_nouns(df, text_column='sentence'):
    okt = Okt()
    df['noun'] = df[text_column].apply(lambda x: " ".join(okt.nouns(str(x))))  # NaN 방지
    return df

def extract_nouns_from_text(text):
    """
    텍스트에서 명사 추출하고 불용어 제거하여 반환
    """

    okt = Okt()

    # 문자열 전처리
    text = str(text).strip()

    # 명사 추출
    nouns = okt.nouns(text)

    # 불용어 제거
    stop_words = ['중', '하기', '되기', '임', '됨']
    filtered_nouns = [word for word in nouns if word not in stop_words]

    return filtered_nouns