import dash
from dash import dcc, html, Input, Output
from django_plotly_dash import DjangoDash
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Django 모델 불러오기
from analysis.models import AnalysisResults
from hobbies.models import HobbyKeywords

# Dash 앱 생성
app = DjangoDash('KeywordBarChart')

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

@app.callback(
    Output('graph-container', 'children'),
    Input('url', 'search')
)
def update_graph(url_search):
    from urllib.parse import parse_qs

    query_params = parse_qs(url_search.lstrip('?'))
    hobby = query_params.get('hobby', ['사진 촬영'])[0]
    gender = query_params.get('gender', ['M'])[0]
    age_group = query_params.get('age_group', ['20s'])[0]
    brand = query_params.get('brand', ['samsung'])[0]
    selected_keywords_str = query_params.get('selected_keywords', ['카메라,배터리,화질'])[0]
    selected_keywords = selected_keywords_str.split(',') if selected_keywords_str else []
    sorted_selected_keywords = sorted(selected_keywords)

    try:
        hobby_entry = HobbyKeywords.objects.get(hobby_name=hobby)
        analysis_entry = AnalysisResults.objects.filter(
            hobby_id=hobby_entry,
            selected_keywords=sorted_selected_keywords
        ).exclude(freq_ratio_samsung={}).exclude(freq_ratio_apple={}).first()

        if not analysis_entry:
            return html.Div("분석 결과가 존재하지 않음")

    except HobbyKeywords.DoesNotExist:
        return html.Div("취미가 존재하지 않음")

    freq_samsung = analysis_entry.freq_ratio_samsung
    freq_apple = analysis_entry.freq_ratio_apple

    keywords = list(freq_samsung.keys())
    samsung_values = list(freq_samsung.values())
    apple_values = list(freq_apple.values())

    # 가장 높은 값이 위로 가게 정렬하고 y축도 반전 필요
    sorted_data = sorted(zip(keywords, samsung_values, apple_values), key=lambda x: x[1], reverse=True)
    keywords, samsung_values, apple_values = zip(*sorted_data)

    fig = make_subplots(rows=1, cols=2, shared_yaxes=True)

    # 삼성 그래프
    fig.add_trace(
        go.Bar(
            x=samsung_values,
            y=keywords,
            orientation='h',
            name='삼성',
            marker=dict(color='#B7E0FF'),
            text=[f"{val:.1f}%" for val in samsung_values],
            textposition='outside',
            hovertemplate='%{y}, %{x:.1f}%<extra></extra>',
            hoverlabel=dict(
                bordercolor='rgba(0,0,0,0)',  # 테두리 제거
                font=dict(color='white', size=14)
            )
        ),
        row=1, col=1
    )

    # 애플 그래프
    fig.add_trace(
        go.Bar(
            x=apple_values,
            y=keywords,
            orientation='h',
            name='애플',
            marker=dict(color='#F4A2C7'),
            text=[f"{val:.1f}%" for val in apple_values],
            textposition='outside',
            hovertemplate='%{y}, %{x:.1f}%<extra></extra>',
            hoverlabel=dict(
                bordercolor='rgba(0,0,0,0)',  # 테두리 제거
                font=dict(color='white', size=14)
            )
        ),
        row=1, col=2
    )

    # 축 및 스타일링 - Y축은 reverse
    fig.update_yaxes(autorange="reversed", row=1, col=1)
    fig.update_yaxes(autorange="reversed", row=1, col=2)
    fig.update_yaxes(showticklabels=False, row=1, col=1)

    # X축 범위 조정 (막대+텍스트가 안 잘리게)
    fig.update_xaxes(
        range=[100, 0],  
        title_font=dict(size=14),
        tickfont=dict(size=12),
        side='bottom',
        row=1, col=1
    )

    # 애플 막대 차트: 왼쪽으로 진행 (우에서 좌)
    fig.update_xaxes(
        range=[0, 100],   
        title_font=dict(size=14),
        tickfont=dict(size=12),
        side='bottom',
        row=1, col=2
    )

    annotations = []
    for idx, keyword in enumerate(keywords):
        annotations.append(
            dict(
                x=0.5,
                y=keyword,
                text=f"<b>{keyword}</b>",  # 굵은 텍스트
                showarrow=False,
                font=dict(
                    size=14,
                    family='Pretendard Variable',  # Pretendard 폰트
                    color='black'
                ),
                xref='paper',
                yref='y1',
                xanchor='center'
            )
        )

    fig.update_layout(
        autosize=True,
        margin=dict(l=20, r=20, t=50, b=50),
        height=None,
        width=None,
        showlegend=False,
        xaxis_title='비율(%)',
        xaxis2_title='비율(%)',
        plot_bgcolor='white',
        paper_bgcolor='white',
        annotations=annotations,  
        bargap=0.1,
        bargroupgap=0.2,
        xaxis=dict(domain=[0.0, 0.4]),
        xaxis2=dict(domain=[0.6, 1.0]),
    )

    return dcc.Graph(
        figure=fig,
        config={'displayModeBar': False, 'responsive': True},
        style={
            'height': '100%',    # 부모 기준 100%로 맞춤
            'width': '100%',     # 부모 기준 100%로 맞춤
            'max-width': '100%', # 부모에 맞게
            'margin': '0 auto',
            'flex': '1 1 auto',
            'minHeight': '400px',
        }
    )
