import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import random
from django_plotly_dash import DjangoDash
from collections import defaultdict
import re

# 앱 생성
app = DjangoDash('HobbyGraph')

# 파스텔 톤 랜덤 색상 생성
def generate_pastel_color():
    r = random.randint(200, 255)
    g = random.randint(200, 255)
    b = random.randint(200, 255)
    return f'rgb({r}, {g}, {b})'

def extract_rank_number(rank_str):
    match = re.search(r"\d+", rank_str)
    return int(match.group()) if match else None

# 기본 라벨 정의
categories = [
    ('10s', 'M'), ('10s', 'F'),
    ('20s', 'M'), ('20s', 'F'),
    ('30s', 'M'), ('30s', 'F'),
    ('40s', 'M'), ('40s', 'F'),
    ('50s', 'M'), ('50s', 'F'),
    ('60s', 'M'), ('60s', 'F')
]

category_labels = [
    '10대<br>남성', '10대<br>여성',
    '20대<br>남성', '20대<br>여성',
    '30대<br>남성', '30대<br>여성',
    '40대<br>남성', '40대<br>여성',
    '50대<br>남성', '50대<br>여성',
    '60대<br>남성', '60대<br>여성'
]

# 기본 데이터 (2024 hobby CSV 참조)
default_raw_data = [
    ('남', '10', 1, '게임'), ('남', '10', 2, '운동'), ('남', '10', 3, '독서'),
    ('여', '10', 1, '음악감상'), ('여', '10', 2, '게임'), ('여', '10', 3, '영상시청'),
    ('남', '20', 1, '게임'), ('남', '20', 2, '운동'), ('남', '20', 3, '독서'),
    ('여', '20', 1, '음악감상'), ('여', '20', 2, '독서'), ('여', '20', 3, '운동'),
    ('남', '30', 1, '게임'), ('남', '30', 2, '운동'), ('남', '30', 3, '음악감상'),
    ('여', '30', 1, '운동'), ('여', '30', 2, '독서'), ('여', '30', 3, '음악감상'),
    ('남', '40', 1, '게임'), ('남', '40', 2, '운동'), ('남', '40', 3, '낚시'),
    ('여', '40', 1, '걷기'), ('여', '40', 2, '영상시청'), ('여', '40', 3, '요리'),
    ('남', '50', 1, '낚시'), ('남', '50', 2, '등산'), ('남', '50', 3, '운동'),
    ('여', '50', 1, '운동'), ('여', '50', 2, '등산'), ('여', '50', 3, '여행'),
    ('남', '60', 1, '등산'), ('남', '60', 2, '바둑'), ('남', '60', 3, '낚시'),
    ('여', '60', 1, '걷기'), ('여', '60', 2, '영상시청'), ('여', '60', 3, '뜨개질')
]

def build_data_dict():
    """기본 데이터로 차트 구성 (TbHobbyRequests 등으로 확장 가능)"""
    data_dict = defaultdict(lambda: [''] * len(categories))
    
    for idx, (age_group, gender) in enumerate(categories):
        kor_gender = '남' if gender == 'M' else '여'
        kor_age = age_group.replace('s', '')
        for _, a, r, hobby in default_raw_data:
            if kor_gender == _ and kor_age == a:
                data_dict[hobby][idx] = f"{r}위"

    return data_dict, category_labels


# Layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Graph(id='hobby-trend-bump-chart', config={'displayModeBar': False},
              style={
            'height': '100%',  # 높이 줄이기
            'width': '100%',      # 너비 줄이기 
            'overflow':'hidden'
        })
])

# 콜백 함수
@app.callback(
    Output('hobby-trend-bump-chart', 'figure'),
    [Input('url', 'search')]
)
def update_chart(url_search):
    from urllib.parse import parse_qs
    query_params = parse_qs(url_search.lstrip('?'))

    # URL 파라미터 추출
    gender = query_params.get('gender', ['M'])[0]
    age_group = query_params.get('age_group', ['20s'])[0]

    data_dict, category_labels = build_data_dict()

    # 파스텔 컬러 매핑
    color_map = {hobby: generate_pastel_color() for hobby in data_dict.keys()}

    fig = go.Figure()

    # 데이터 순회해서 추가
    for hobby, ranks_list in data_dict.items():
        x = []
        y = []
        for idx, rank in enumerate(ranks_list):
            if rank:
                x.append(category_labels[idx])
                rank_number = extract_rank_number(rank)
                if rank_number:
                    y.append(rank_number)
        
        if x:
            fig.add_trace(go.Scatter(
                x=x,
                y=y,
                mode='markers+text',
                text=[hobby]*len(x),  # 취미명만 출력
                textposition='middle center',
                marker=dict(
                    size=60,
                    color=color_map[hobby],
                    # line=dict(width=2, color='white')
                ),
                hoverinfo='skip',
                name=hobby
            ))


    fig.update_layout(
        # 레이아웃 설정
        title=None,
        xaxis=dict(
            title=None,
            tickangle=0,
            tickfont=dict(size=14),
            showline=True,
            linewidth=2,
            linecolor='black',
            showgrid=False
        ),
        yaxis=dict(
            title=None,
            tickvals=[1, 2, 3],
            ticktext=['1위', '2위', '3위'],
            autorange='reversed',
            tickfont=dict(size=16),
            showline=True,
            linewidth=2,
            linecolor='black',
            showgrid=False
        ),
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=80, r=50, t=50, b=20),
        height=350,
        autosize=True,
    )

    return fig



# # ----- [실제 데이터] -----
    
    # # 카테고리 정의
    # categories = [
    # ('10s', 'M'), ('10s', 'F'),
    # ('20s', 'M'), ('20s', 'F'),
    # ('30s', 'M'), ('30s', 'F'),
    # ('40s', 'M'), ('40s', 'F'),
    # ('50s', 'M'), ('50s', 'F'),
    # ('60s', 'M'), ('60s', 'F')
    # ]

    # # 시각화용 카테고리 라벨 (x축 표시값)
    # category_labels = [
    #     '10대<br>남성', '10대<br>여성',
    #     '20대<br>남성', '20대<br>여성',
    #     '30대<br>남성', '30대<br>여성',
    #     '40대<br>남성', '40대<br>여성',
    #     '50대<br>남성', '50대<br>여성',
    #     '60대<br>남성', '60대<br>여성'
    # ]

    # # 취미 가져오기
    # hobbies = HobbyKeywords.objects.all()
    # data_dict = {hobby.hobby_name: [] for hobby in hobbies}

    # # 각 카테고리별 취미 순위 계산
    # for idx, (cat_age_group, cat_gender) in enumerate(categories):
    #     queryset = (
    #         HobbyTrends.objects
    #         .filter(age_group=cat_age_group, gender=cat_gender)
    #         .values('hobby_id')
    #         .annotate(total_count=Sum('count'))
    #         .order_by('-total_count')
    #     )

    #     ranked_hobby_ids = [entry['hobby_id'] for entry in queryset[:3]]
    #     rank_map = {hobby_id: f"{rank+1}위" for rank, hobby_id in enumerate(ranked_hobby_ids)}

    #     for hobby in hobbies:
    #         rank_label = rank_map.get(hobby.hobby_id, None)
    #         data_dict[hobby.hobby_name].append(rank_label)
    

    # ----- [임시 테스트 데이터] -----
    
    # categories = [
    # '10대<br>남성', '10대<br>여성', '20대<br>남성', '20대<br>여성',
    # '30대<br>남성', '30대<br>여성', '40대<br>남성', '40대<br>여성',
    # '50대<br>남성', '50대<br>여성', '60대<br>남성', '60대<br>여성'
    # ]

    # ranks = ['1위', '2위', '3위']

    # data_dict = {
    # '게임': ['1위', '1위', '1위', '2위', '1위', '2위', '1위', '3위', '3위', '2위', '1위', '2위'],
    # '독서': ['2위', '2위', '2위', '1위', '2위', '1위', '2위', '3위', '3위', '3위', '3위', '3위'],
    # '운동': ['3위', '3위', '3위', '3위', '3위', '3위', '3위', '1위', '1위', '1위', '2위', '1위'],
    # '음악감상': ['1위', '1위', '1위', '1위', '1위', '1위', '1위', '1위', '1위', '1위', '1위', '1위'],
    # '영상시청': ['2위', '2위', '2위', '2위', '2위', '2위', '2위', '2위', '2위', '2위', '2위', '2위'],
    # '등산': ['3위', '3위', '3위', '3위', '3위', '3위', '3위', '3위', '3위', '3위', '3위', '3위'],
    # '요리': ['1위', '2위', '3위', '1위', '2위', '3위', '1위', '2위', '3위', '1위', '2위', '3위'],
    # '바둑': ['3위', '1위', '2위', '3위', '1위', '2위', '3위', '1위', '2위', '3위', '1위', '2위'],
    # '낚시': ['2위', '3위', '1위', '2위', '3위', '1위', '2위', '3위', '1위', '2위', '3위', '1위'],
    # '뜨개질': ['1위', '3위', '2위', '1위', '3위', '2위', '1위', '3위', '2위', '1위', '3위', '2위'],
    # }