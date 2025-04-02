# 📱 스마트폰 리뷰 기반 맞춤형 추천 시스템 프로젝트

사용자 리뷰와 유튜브 영상 데이터를 수집하고 분석하여, 사용자의 취향에 맞는 스마트폰을 추천해주는 웹 서비스

- 💬 리뷰 데이터에서 핵심 키워드 및 감성 분석
- 🤖 LLM 기반의 RAG 기술을 활용한 자연스러운 추천 문구 생성
- 🛠 ETL부터 시각화까지 자동화된 데이터 처리 파이프라인 구축

## 🔧 서비스 기능

- 📊 스마트폰 리뷰 크롤링 (다나와, 유튜브 api)
- 🔄 ETL 자동화 파이프라인 구축 (Apache Airflow 기반)
- 📂 대용량 데이터 저장 및 분산처리 (HDFS + Spark 활용)
- 🧼 데이터 전처리 및 감성 분석 (Spark, Pandas)
- 🧠 LLM 기반 RAG 추천 시스템 (Chroma + OpenAI)
- 💡 Django 기반 사용자 맞춤형 추천 결과 제공
- 📈 분석 시각화 (django-plotly-dash)

## 🛠 기술 스택

| 목적 | 사용 기술 |
|------|-----------|
| 워크플로우 자동화 | Apache Airflow |
| 데이터 수집 | YouTube API, Selenium |
| 데이터 처리 및 분석 | PySpark, Pandas |
| 저장소 | HDFS, MySQL |
| LLM 활용 | OpenAI API, Chroma Vector DB |
| 웹 서비스 | Django |
| 시각화 | Django-Plotly-Dash |
| 기타 | Git, Jupyter Notebook, AWS |

## 🖼 프로젝트 아키텍처
![image](./images/architecture.png)
![image](./images/web_architecture.png)

## 🗂 프로젝트 파일 구조

```bash
PhoneRecommender/
├── airflow/                       # Airflow DAG 및 자동화 스크립트
│   ├── dags/                      # ETL 워크플로우 정의
│   ├── danawa_data/               # 다나와 수집 데이터
│   └── youtube_data/              # 유튜브 수집 데이터
│
├── web_project/                   # Django 기반 웹 서비스
│   ├── analysis/                  # 분석 기능 앱
│   ├── config/                    # Django 설정
│   ├── crawled_data/              # 크롤링 데이터
│   ├── data/                      # RAG용 최신 폰 기종 데이터
│   ├── dash_apps/                 # Dash 기반 시각화 앱
│   ├── hobbies/                   # 사용자 취향 관련 앱
│   ├── users/                     # 사용자 관리 앱
│   ├── utils/                     # 함수 및 유틸 모음
│   ├── templates/                 # HTML 템플릿
│   ├── static/                    # CSS, JS 등 정적 파일
│   ├── manage.py                  # Django 실행 스크립트
│   └── requirements.txt           # 백엔드 의존 패키지 목록
│
├── notebooks/                     # Jupyter 분석 노트북 및 코드
│   ├── db_setup/                  # DB 초기화 및 테이블 설정
│   ├── data_pipeline/             # HDFS → Spark → MySQL ETL 파이프라인
│   ├── data_analysis/             # 리뷰 및 유튜브 데이터 분석
│   ├── llm_workflow/              # 키워드 추출, LLM 결과 저장 등
│   └── datasets/                  # CSV, 엑셀 등 학습/분석용 데이터
│
├── images/                        # 아키텍처 및 시연 스크린샷
│   └── architecture.png
│   └── web_screenshots
├── .gitignore                     # 업로드 제외 파일 목록
└── README.md                      # 프로젝트 개요 및 설명

```
