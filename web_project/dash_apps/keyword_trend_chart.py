import dash
from dash import dcc, html, Input, Output
from django_plotly_dash import DjangoDash
import plotly.graph_objs as go
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Django 모델
from analysis.models import TbAnalysisResults
from hobbies.models import TbHobbies

# Dash 앱 생성
app = DjangoDash('KeywordTrendChart')

# 기본 레이아웃
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='graph-container', style={
        'width': '100%',
        'height': '100%',
    }),
], style={
    'width': '100%',
    'height': '100%',
})

# 랜덤 색상 생성 함수 
fixed_colors = [
    "#A9E3A4",  
    "#F2A0F1",  
    "#99C3F3",  
    "#F2C49B",  
    "#F04747", 
]

def get_fixed_colors(keywords):
    keyword_colors = {}
    
    for idx, keyword in enumerate(keywords):
        keyword_colors[keyword] = fixed_colors[idx % len(fixed_colors)]
    
    return keyword_colors

@app.callback(
    Output('graph-container', 'children'),
    [Input('url', 'search')]
)
def update_trend_graph(url_search):
    from urllib.parse import parse_qs

    query_params = parse_qs(url_search.lstrip('?'))
    hobby = query_params.get('hobby', ['사진 촬영'])[0]
    brand = query_params.get('brand', ['samsung'])[0]
    selected_keywords_str = query_params.get('selected_keywords', [''])[0]
    selected_keywords = selected_keywords_str.split(',') if selected_keywords_str else []
    sorted_selected_keywords = sorted(selected_keywords)

    try:
        hobby_entry = TbHobbies.objects.get(hobby_name=hobby)
        analysis_entry = TbAnalysisResults.objects.filter(
            hobby=hobby_entry,
            keywords=sorted_selected_keywords
        ).order_by('-updated_at').first()
        
        if not analysis_entry:
            return html.Div("분석 결과 없음")

        trend_data = (analysis_entry.monthly_trends or {}).get(brand, {})
        months_datetime = sorted([datetime.strptime(m, "%Y-%m") for m in trend_data.keys()])
        recent_months_datetime = months_datetime[-6:]
        months = [dt.strftime("%Y-%m") for dt in recent_months_datetime]

        keywords = analysis_entry.keywords or []

        # 랜덤 색상 매핑
        keyword_colors = get_fixed_colors(keywords)

        # 그래프 생성
        fig = go.Figure()

        # 모든 월을 포함한 리스트 생성 (예: 최근 6개월)
        all_months = [datetime.now() - relativedelta(months=i+1) for i in range(6)]
        all_months_str = [dt.strftime("%Y-%m") for dt in all_months]

        # 그래프에 들어갈 y_values 준비
        for idx, keyword in enumerate(keywords):
            y_values = [
                round(trend_data.get(month, {}).get(keyword, {}).get('ratio', 0) * 100, 2) 
                if month in trend_data else 0  # 데이터가 없는 월에 대해 0 처리
                for month in all_months_str
            ]

            color = keyword_colors[keyword]  # 랜덤 색상

            fig.add_trace(go.Scatter(
                x=all_months_str,
                y=y_values,
                mode='lines+markers',
                name=keyword,
                line=dict(
                    shape='linear',
                    color=color,  # 선 색상
                    width=3
                ),
                marker=dict(
                    symbol='circle',
                    size=6,
                    color=color,  # 마커 색상
                    line=dict(width=2, color='white')  # 마커 테두리 색상
                ),
                text=[keyword] * len(all_months_str),
                hoverlabel=dict(
                    bgcolor=color,
                    bordercolor=color,
                    font_size=14,
                    font_color="white"  
                ),
                hovertemplate='%{text}, %{y:.1f}%<extra></extra>'
            ))
            
        # 공통 trace hover 스타일
        fig.update_traces(
            hovertemplate='%{text}, %{y:.1f}%<extra></extra>'
        )

        # 그래프 레이아웃 설정
        fig.update_layout(
            autosize=True,
            margin=dict(l=80, r=0, t=80, b=80),
            height=200,
            width=None,
            xaxis=dict(
                tickformat='%Y-%m',
                tickmode='array',
                tickvals=all_months_str,
                ticktext=all_months_str,
                tickfont=dict(size=14),
                showgrid=True,
                gridcolor='lightgrey'
            ),
            yaxis=dict(
                tickfont=dict(size=14),
                showgrid=True,
                gridcolor='lightgrey',
                range=[-10, 110],
            ),
            annotations=[
                # y축 라벨 (비율)
                dict(
                    text="비율(%)",
                    x=-0.09,    
                    y=1.05,    
                    xref='paper',
                    yref='paper',
                    showarrow=False,
                    font=dict(size=14, color='black'),
                    xanchor='left',     
                    yanchor='top' 
                ),
                # X축 라벨 (월)
                dict(
                    text="월",
                    x=1.02,    
                    y=-0.15,   
                    xref='paper',
                    yref='paper',
                    showarrow=False,
                    font=dict(size=14, color='black'),
                    xanchor='right',
                    yanchor='bottom'
                ),
            ],
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.5,
                xanchor="left",
                x=1.05,  
                font=dict(size=14)
            ),
            showlegend=True,
        )

        return dcc.Graph(
            figure=fig,
            config={'displayModeBar': False, 'responsive': True},
            style={
                'height': '500px',    
                'width': '100%',     
                'max-width': '100%', 
                'margin': '0 auto',
                'flex': '1 1 auto',
                'minHeight': '200px',
            }
        )
    
    except Exception as e:
        print("[ERROR]:", e)
        return html.Div("에러 발생!")
