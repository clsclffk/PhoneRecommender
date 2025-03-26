import dash
from dash import dcc, html, Input, Output
from django_plotly_dash import DjangoDash
import plotly.graph_objs as go
from datetime import datetime
from urllib.parse import parse_qs

# Django 모델
from analysis.models import AnalysisResults
from hobbies.models import HobbyKeywords

# DjangoDash 앱 이름
app = DjangoDash('SentimentBarChart',
                 serve_locally=True,)

# 기본 레이아웃
app.layout = html.Div(
    style={'padding': '0', 'margin': '0'},   # 전체 감싸는 Div에 여백 제거
    children=[
        dcc.Location(id='url', refresh=False),

        html.Div(
            id='sentiment-bar-container',
            style={'padding': '0', 'margin': '0'}   # 내부 그래프 여백 제거
        ),

        html.Div(
            id='month-slider-container',
            style={
                'padding': '0px 25px 10px',   # 슬라이더 컨테이너 내부 여백 제거
                'margin': '0',     # 슬라이더 컨테이너 외부 여백 제거
                # 'backgroundColor': '#e5f6d0'
            }
        ),

    ]
)

# 최근 6개월 필터링 함수
def get_recent_filtered_months(trend_data):
    filtered_months = []
    for month, keyword_data in trend_data.items():
        if not keyword_data:
            continue

        valid_data = any(
            (kw.get('pos_ratio', 0) > 0 or kw.get('neg_ratio', 0) > 0)
            for kw in keyword_data.values()
        )

        if valid_data:
            filtered_months.append(month)

    if not filtered_months:
        return []

    # 날짜 정렬 후 최근 6개월
    filtered_months_datetime = sorted([
        datetime.strptime(month, "%Y-%m") for month in filtered_months
    ])

    recent_months_datetime = filtered_months_datetime[-6:]
    recent_months = [dt.strftime("%Y-%m") for dt in recent_months_datetime]

    return recent_months

# 슬라이더 콜백
@app.callback(
    Output('month-slider-container', 'children'),
    [Input('url', 'search')]
)
def update_month_slider(url_search):
    query_params = parse_qs(url_search.lstrip('?'))
    hobby = query_params.get('hobby', ['사진 촬영'])[0]
    brand = query_params.get('brand', ['samsung'])[0]
    selected_keywords_str = query_params.get('selected_keywords', [''])[0]
    selected_keywords = selected_keywords_str.split(',') if selected_keywords_str else []

    try:
        hobby_entry = HobbyKeywords.objects.get(hobby_name=hobby)
        analysis_entry = AnalysisResults.objects.filter(
            hobby_id=hobby_entry,
            selected_keywords=sorted(selected_keywords)
        ).order_by('-created_at').first()

        if not analysis_entry:
            return html.Div("분석 결과 없음")

        trend_data = analysis_entry.keyword_monthly_trend.get(brand, {})

        # 최근 6개월 필터링
        recent_months = get_recent_filtered_months(trend_data)

        if not recent_months:
            return html.Div("해당 브랜드에 대한 감성 데이터가 없습니다!")

        return html.Div(   # 슬라이더를 감싸는 Div 추가
            dcc.Slider(
                id='month-slider',
                min=0,
                max=len(recent_months) - 1,
                marks={i: month.replace('-', '\u2011') for i, month in enumerate(recent_months)},
                value=len(recent_months) - 1,
                # tooltip={"placement": "bottom", "always_visible": False},
                updatemode='mouseup',
                className='rc-slider custom-slider'
            ),
            style={
                'padding': '0',
                'margin': '0'
            }
        )
    except Exception as e:
        print("[ERROR]:", e)
        return html.Div("에러 발생!")

# 메인 그래프 콜백
@app.callback(
    Output('sentiment-bar-container', 'children'),
    [Input('url', 'search'),
     Input('month-slider', 'value')]
)
def update_sentiment_bar(url_search, selected_month_idx):
    query_params = parse_qs(url_search.lstrip('?'))
    hobby = query_params.get('hobby', ['사진 촬영'])[0]
    brand = query_params.get('brand', ['samsung'])[0]
    selected_keywords_str = query_params.get('selected_keywords', [''])[0]
    selected_keywords = selected_keywords_str.split(',') if selected_keywords_str else []

    try:
        hobby_entry = HobbyKeywords.objects.get(hobby_name=hobby)
        analysis_entry = AnalysisResults.objects.filter(
            hobby_id=hobby_entry,
            selected_keywords=sorted(selected_keywords)
        ).order_by('-created_at').first()

        if not analysis_entry:
            return html.Div("분석 결과 없음")

        trend_data = analysis_entry.keyword_monthly_trend.get(brand, {})
        if not trend_data:
            return html.Div("해당 브랜드에 대한 감성 데이터가 없습니다!")

        # 최근 6개월 필터링
        recent_months = get_recent_filtered_months(trend_data)

        if not recent_months:
            return html.Div("해당 월에 대한 감성 데이터가 없습니다!")

        selected_month = recent_months[int(selected_month_idx)]
        print("[DEBUG] selected_month:", selected_month)

        # 선택한 월의 키워드 감성 데이터
        month_data = trend_data[selected_month]
        keywords = list(month_data.keys())

        pos_values = []
        neg_values = []

        for keyword in keywords:
            keyword_info = month_data[keyword]
            pos_ratio = round(keyword_info.get('pos_ratio', 0) * 100, 2)
            neg_ratio = round(keyword_info.get('neg_ratio', 0) * 100, 2)

            pos_values.append(pos_ratio)
            neg_values.append(neg_ratio)

        fig = go.Figure()

        # 긍정 막대
        fig.add_trace(go.Bar(
            x=keywords,
            y=pos_values,
            name='긍정',
            marker_color='#47C1F7',  # 하늘색
            hovertemplate=
                '<b>%{x}</b><br>' +
                '긍정: %{y:.1f}%<extra></extra>',
            hoverlabel=dict(
                bgcolor='#47C1F7',  # 하늘색 배경
                bordercolor='rgba(0,0,0,0)', 
                font=dict(color='white', size=13)
            )
        ))

        # 부정 막대
        fig.add_trace(go.Bar(
            x=keywords,
            y=neg_values,
            name='부정',
            marker_color='#F77369',  # 분홍색
            hovertemplate=
                '<b>%{x}</b><br>' +
                '부정: %{y:.1f}%<extra></extra>',
            hoverlabel=dict(
                bgcolor='#F77369',  # 분홍색 배경
                bordercolor='rgba(0,0,0,0)', 
                font=dict(color='white', size=13)
            )
        ))

        # 전역 hoverlabel 스타일
        fig.update_layout(
            autosize=True,
            barmode='stack',
            height=None,
            width=None,
            margin=dict(l=10, r=10, t=50, b=50),

            # 범례 위치 및 스타일
            legend=dict(
                orientation="v",
                yanchor="bottom",
                y=0,
                xanchor="left",
                x=1.05,
                font=dict(size=14)
            ),

            xaxis=dict(
                tickmode='auto',
                tickfont=dict(size=12)
            ),
            yaxis=dict(
                tickfont=dict(size=12)
            ),
            annotations=[
                dict(
                    text="비율(%)",
                    x=-0.05,
                    y=1.05,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=14),
                    align='left')
            ],
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        return dcc.Graph(
            figure=fig,
            config={
                'displayModeBar': False  # 툴바 삭제
            },
            style={
                'height': '100%',    # 부모 기준 100%로 맞춤
                'width': '100%',     # 부모 기준 100%로 맞춤
                'max-width': '100%', # 부모에 맞게
                # 'margin': '0 auto',
                'flex': '1 1 auto',
                'minHeight': '400px',
            }
        )

    except Exception as e:
        import traceback
        print("[ERROR]:", e)
        traceback.print_exc()
        return html.Div("에러 발생!")
    
