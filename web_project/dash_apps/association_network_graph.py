import dash
from dash import dcc, html, Input, Output
from django_plotly_dash import DjangoDash
import plotly.graph_objs as go
import networkx as nx

app = DjangoDash('KeywordNetworkGraph')

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='network-graph-container')
])

@app.callback(
    Output('network-graph-container', 'children'),
    [Input('url', 'search')]
)

def update_network_graph(url_search):

    from urllib.parse import parse_qs
    query_params = parse_qs(url_search.lstrip('?'))

    print("====== 쿼리 파라미터 ======")
    print(query_params)

    hobby = query_params.get('hobby', ['사진 촬영'])[0]
    gender = query_params.get('gender', ['M'])[0]
    age_group = query_params.get('age_group', ['20s'])[0]
    brand_param = query_params.get('brand', ['samsung'])[0]
    selected_keywords_str = query_params.get('selected_keywords', [''])[0]
    selected_keywords_list = selected_keywords_str.split(',')
    selected_keywords_sorted = sorted(selected_keywords_list)

    print(f"hobby: {hobby}, gender: {gender}, age_group: {age_group}, brand: {brand_param}")

    import json
    from analysis.models import TbAnalysisResults
    from hobbies.models import TbHobbies
    try:
        hobby_entry = TbHobbies.objects.get(hobby_name=hobby)
        analysis_entry = TbAnalysisResults.objects.filter(
            hobby=hobby_entry,
            keywords=selected_keywords_sorted
        ).order_by('-updated_at').first()
        if not analysis_entry:
            return html.Div("분석 결과가 존재하지 않습니다.")
        summaries = {}
        if analysis_entry.summaries:
            try:
                summaries = json.loads(analysis_entry.summaries)
            except (TypeError, json.JSONDecodeError):
                pass
        related_words_samsung = summaries.get('related_words_samsung') or {}
        related_words_apple = summaries.get('related_words_apple') or {}
    except (TbHobbies.DoesNotExist, TbAnalysisResults.DoesNotExist):
        return html.Div("분석 결과가 존재하지 않음")
    
    if brand_param == 'samsung':
        related_words_data = related_words_samsung
        center_color = '#163E64'
        highlight_node_color = '#4E95D9'
        node_color = '#B7E0FF'
        brand = '삼성'
    else:
        related_words_data = related_words_apple
        center_color = '#B3116E'
        highlight_node_color = '#F4A2C7'
        node_color = '#FCE4EE'
        brand = '애플'

    center_node = related_words_data['center']
    keywords = related_words_data['related_words']

    highlight_keywords = keywords[:5]

    G = nx.Graph()
    center_node = hobby
    G.add_node(center_node)

    for keyword in keywords:
        G.add_node(keyword)
        G.add_edge(center_node, keyword)

    # 포지션 값 스케일 확대
    # scale : 전체 그래프 퍼짐 정도
    # k : 노드간 최적 거리
    pos = nx.spring_layout(G, scale=2, k=0.35)

    # X/Y 좌표 추출 
    x_vals = [coord[0] for coord in pos.values()]
    y_vals = [coord[1] for coord in pos.values()]

    # 패딩 및 범위 계산
    padding = 0.45
    x_range = [min(x_vals) - padding, max(x_vals) + padding]
    y_range = [min(y_vals) - padding, max(y_vals) + padding]

    shapes = []
    annotations = []

    # 엣지 그리기 (shapes)
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        shapes.append(dict(
            type='line',
            x0=x0, y0=y0,
            x1=x1, y1=y1,
            line=dict(width=1.5, color='#888'),
            layer='below'
        ))

    # 노드색 다르게 주기
    for node in G.nodes():
        x, y = pos[node]
        text_length = len(node)

        # 중심 노드 크기 조정
        if node == center_node:
            width = text_length * 0.2 + 0.6
            height = 0.5
            font_size = 14
            color = center_color
            text_color = 'white'

        elif node in highlight_keywords:
            width = text_length * 0.1 + 0.5
            height = 0.35
            font_size = 12
            color = highlight_node_color
            text_color = 'black'

        else:
            width = text_length * 0.08 + 0.4   # 0.1 → 0.08 / 0.5 → 0.4 (더 작게!)
            height = 0.3                       # 0.35 → 0.3
            font_size = 10  
            color = node_color
            text_color = 'black'   

        # 둥근 정도도 비율에 맞게 (너비에 비례)
        rx = min(width, height) * 0.2

        # 둥근 사각형 path 생성
        rounded_rect_path = (
            f"M {x - width/2 + rx},{y - height/2} "
            f"L {x + width/2 - rx},{y - height/2} "
            f"Q {x + width/2},{y - height/2} {x + width/2},{y - height/2 + rx} "
            f"L {x + width/2},{y + height/2 - rx} "
            f"Q {x + width/2},{y + height/2} {x + width/2 - rx},{y + height/2} "
            f"L {x - width/2 + rx},{y + height/2} "
            f"Q {x - width/2},{y + height/2} {x - width/2},{y + height/2 - rx} "
            f"L {x - width/2},{y - height/2 + rx} "
            f"Q {x - width/2},{y - height/2} {x - width/2 + rx},{y - height/2} "
            f"Z"
        )

        shapes.append(dict(
        type='path',
        path=rounded_rect_path,  # 둥근 사각형 경로
        fillcolor=color,
        line=dict(color='rgba(0,0,0,0)', width=0),
        layer='above'  
        ))

        annotations.append(dict(
            x=x,
            y=y,
            text=node,
            showarrow=False,
            font=dict(size=16, color=text_color),
            xanchor='center',
            yanchor='middle'
        ))

    fig = go.Figure(
        layout=go.Layout(
            showlegend=False,
            autosize=False, 
            height=600,
            width=600, 
            margin=dict(b=0, l=0, r=0, t=0),
            plot_bgcolor='white',
            paper_bgcolor='white',
            shapes=shapes,
            annotations=annotations,
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                fixedrange=True,
                scaleanchor='y',    # x축 기준으로 y축 비율 고정
                domain=[0, 1],      # x축 전체 화면에 차지
                range=x_range,  # 왼쪽 잘림 방지 (범위를 넉넉히 줘야함!)
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                fixedrange=True,
                domain=[0, 1],      # y축 전체 화면에 차지
                range=y_range  # 위아래도 여유 있게!
            ),
        )
    )

    return dcc.Graph(
        figure=fig,
        config={'displayModeBar': False, 'responsive': True},
        style={
            'height': '600px',     # iframe과 동일
            'width': '600px',      # iframe과 동일
            'padding': '0',        # 패딩 제거
            'margin': '0 auto',    # 가운데 정렬
            'display': 'block'     # inline-block이 아니라 block 처리
        }
    )
