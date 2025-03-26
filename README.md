# 프로젝트 개요

## 🔧 서비스 기능

- 📊 스마트폰 리뷰 크롤링 (다나와, 유튜브 api)
- 🔄 ETL 자동화 파이프라인 구축 (Apache Airflow 기반)
- 📂 대용량 데이터 저장 및 분산처리 (HDFS + Spark 활용)
- 🧼 데이터 전처리 및 감성 분석 (Spark, Pandas)
- 🧠 LLM 기반 RAG 추천 시스템 (Chroma + OpenAI)
- 💡 Django 기반 사용자 맞춤형 추천 결과 제공
- 📈 분석 시각화 (Dash, Plotly)

## 🗂 프로젝트 파일 구조

```bash
PhoneRecommender/
├── airflow/           # DAG 기반 자동화 파이프라인
├── web_project/       # Django + 분석 + 추천 웹 서비스
└── README.md
```

## 🖼 프로젝트 아키텍처
![image](./images/architecture.png)
