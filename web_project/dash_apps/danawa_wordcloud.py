from django_plotly_dash import DjangoDash
from dash import html, dcc, Output, Input
import pandas as pd
from collections import Counter
from crawled_data.models import TbprocessedDanawa
from wordcloud import WordCloud
import base64
from io import BytesIO
import random
from urllib.parse import urlparse, parse_qs

# 커스텀 불용어 리스트
custom_stopwords = ['갤럭시', '이벤트', '휴대폰', '진짜' ,'역시', '더', '아주', '플러스', '배송', '울트라',
                   '어머니', '기존', '매우', '완전', '기본', '삼성', '전자', '핸드폰', '원래', '처음', '아이폰',
                   '다시', '자급', '사용','시리즈', '구매', '반품', '이번', '계속', '하면', '구입', '참여', '선물', '지금', '제품',
                   '가장', '차이', '생각', '매장', '신세계', '보고', '정말', '마음', '고민', '최고', '스마트폰', '이전', '변경',
                   '데이터', '픽업', '기능', '성능', '듭니', '항상', '혜택', '제일', '만족', '비교', '가지' ,'사은', '주문', '선택', 
                    '센터', '다행', '굳이', '부분', '한지', '상황', '개인', '기준', '모델', '정도', '무엇', '부분', '후회', '어차피', '거듭',
                    '타입', '반값', '사전예약', '가지', '커서', '고객', '문의', '이제', '강남','투폰', '반면', '안남', '전혀', '율도', '햐긴참',
                   '사실', '하이마트', '제약', '그레이', '제로', '결정', '엣지', '홈페이지', '제로', '하나', '별로', '안테나', '프로', '조건', 
                   '택배', '스마트스토어', '나날이', '최근', '신사', '대박', '자꾸', '줄라', '마린', '자꾸', '아이디', '바람', '잔고', '적응',
                   '때문', '그냥', '동시', '사이트', '쿠통', '보급', '먼저', '할인', '애플', '베이지', '블랙', '스스로', '스토어', '가입', '태그',
                   '하니', '지원', '개통', '가입', '계획', '핑크', '베스', '합의', '신청', '공홈', '보이', '출시', '카드', '최신', '블루', '맥스',
                   '옐로우', '쿠폰', '플립', '차별', '노트', '다음', '추가', '교체', '직접', '부가', '중소기업', '전용' ,'스마트', '안드로이드', '살짝',
                   '공식', '우선', '가족', '일반', '어쨌든', '지향', '적용', '평가', '달달', '경로', '판매', '한국', '안내', '정품', '마침', '제공',
                   '하루', '처럼', '사람', '온라인', '소비자', '이자', '상이', '쓰기', '개월', '적립', '행사', '어플', '엘지', '민팃', '확장', '대기',
                   '컨트롤', '사고', '안해', '예전', '세이프', '구한', '정신승리', '평생', '매직', '계열', '미니', '덕분', '차로', '방문', '작고',
                   '런가', '번가', '양품', '장점', '기변', '걱정', '설정', '연령', '오니', '측면', '재고', '스토어', '순차', '쿠팡', '모든', '상태',
                   '측면', '완료', '예정', '화이트', '도착', '개도', '여기', '데저트', '기도', '한참', '밤새', '손목', '마이', '타령', '추천', '아들', '크게',
                   '리뷰', '돌이', '중고', '설명', '처리', '그램', '바꿈', '갑자기', '사면', '골드', '신제품', '자체', '포장', '아픔', '문제', '이상', '에쓰', '할부',
                    '아이', '일자', '내용', '기분', '물량', '이오', '주식', '조일이', '생애', '자손', '줄줄', '버벅임', '야호', '제조',
                     '토스', '사용자', '기간', '가끔', '건가', '아무', '증권', '튕기기', '요즘', '거거익선', '그게', '퍼플', '물건', '페이지', '이후', '포기', '예약', '박스',
                     '메인', '세영', '안나', '실망', '이슈', '엉망', '사서', '살때', '젤루', '적립금', '주시',  ]

# 파란 계열 색상 함수 (만족)
def blue_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    # 기준 하늘색을 HSL로 변환한 후, 채도와 밝기를 랜덤하게 변형
    hue = 200  # 하늘색의 기준 색상 (HSL에서의 Hue 값)
    saturation = random.randint(70, 100)  # 채도 (70~100% 사이)
    lightness = random.randint(40, 60)  # 밝기 (40~60% 사이)
    return f"hsl({hue}, {saturation}%, {lightness}%)"

# 빨간 계열 색상 함수 (불만족)
def red_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    # 기준 분홍색을 HSL로 변환한 후, 채도와 밝기를 랜덤하게 변형
    hue = 0  # 분홍색의 기준 색상 (HSL에서의 Hue 값)
    saturation = random.randint(70, 100)  # 채도 (70~100% 사이)
    lightness = random.randint(40, 60)  # 밝기 (40~60% 사이)
    return f"hsl({hue}, {saturation}%, {lightness}%)"


# 워드클라우드 생성 함수 (sentiment_label 추가)
def create_wordcloud_image(noun_series, stopwords, sentiment_label, font_path="/home/lab13/.fonts/pretendard/Pretendard-Regular.otf", top_n=30):
    text = ' '.join(noun_series.dropna())
    word_list = text.split()
    filtered_words = [word for word in word_list if word not in stopwords and len(word) > 1]
    word_counts = Counter(filtered_words)
    top_words = dict(word_counts.most_common(top_n))

    wordcloud = WordCloud(
        background_color='white',
        font_path=font_path,
        width=600,
        height=500
    ).generate_from_frequencies(top_words)

    # 만족(1): 파랑, 불만족(0): 빨강
    if sentiment_label == '1':
        wordcloud.recolor(color_func=blue_color_func)
    else:
        wordcloud.recolor(color_func=red_color_func)

    buffer = BytesIO()
    wordcloud.to_image().save(buffer, format='png')
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"

# =============================
# 삼성 워드클라우드 앱
# =============================

app_samsung = DjangoDash(name='DanawaWordCloudSamsung')

app_samsung.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        html.Div([
            html.Img(id='samsung-wordcloud', style={'width': '100%', 'height': 'auto','objectFit': 'contain' })
        ], className='wordcloud-box')
    ], className='wordcloud-container')
])

@app_samsung.callback(
    Output('samsung-wordcloud', 'src'),
    Input('url', 'href')
)
def update_samsung_wordcloud(href):
    # 기본값은 '1' (만족)
    sentiment_label = '1'
    
    if href:
        parsed_url = urlparse(href)
        query_params = parse_qs(parsed_url.query)
        sentiment_label = query_params.get('sentiment_label', ['1'])[0]

    print(f"삼성 URL에서 받은 sentiment_label 값: {sentiment_label}")

    qs = TbprocessedDanawa.objects.filter(sentiment_label=sentiment_label, brand='samsung')
    df = pd.DataFrame(list(qs.values('noun')))

    print("삼성 쿼리셋 개수:", qs.count())
    print(df.head())

    samsung_wc = create_wordcloud_image(df['noun'], custom_stopwords, sentiment_label)
    return samsung_wc

# =============================
# 애플 워드클라우드 앱
# =============================

app_apple = DjangoDash(name='DanawaWordCloudApple')

app_apple.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        html.Div([
            html.Img(id='apple-wordcloud', style={'width': '100%', 'height': 'auto','objectFit': 'contain' })
        ], className='wordcloud-box')
    ], className='wordcloud-container')
])

@app_apple.callback(
    Output('apple-wordcloud', 'src'),
    Input('url', 'href')
)
def update_apple_wordcloud(href):
    # 기본값은 '1' (만족)
    sentiment_label = '1'
    
    if href:
        parsed_url = urlparse(href)
        query_params = parse_qs(parsed_url.query)
        sentiment_label = query_params.get('sentiment_label', ['1'])[0]

    print(f"애플 URL에서 받은 sentiment_label 값: {sentiment_label}")

    qs = TbprocessedDanawa.objects.filter(sentiment_label=sentiment_label, brand='apple')
    df = pd.DataFrame(list(qs.values('noun')))

    print("애플 쿼리셋 개수:", qs.count())
    print(df.head())

    apple_wc = create_wordcloud_image(df['noun'], custom_stopwords, sentiment_label)
    return apple_wc