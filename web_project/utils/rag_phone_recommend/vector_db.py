import pandas as pd
import os
import openai
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

# 폰 기종 파일 저장 위치
EXCEL_PATH = '/home/lab13/web_project/data/phone_models.xlsx'

# 벡터DB 저장 위치
CHROMA_DB_DIR = '/home/lab13/web_project/vector_db/'

# OpenAI API Key 설정
openai_api_key = os.environ.get("OPENAI_API_KEY")

# 클라이언트 생성
client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# 컬렉션 이름
collection_name = "phone_models"

# 기존 컬렉션 삭제 (있을 경우)
try:
    client.delete_collection(name=collection_name)
    print(f"기존 컬렉션 '{collection_name}' 삭제 완료")
except Exception as e:
    print(f"컬렉션 삭제 중 오류 발생 (무시 가능): {e}")

# 임베딩 함수 정의
embedding_function = OpenAIEmbeddingFunction(
    api_key=openai_api_key,
    model_name="text-embedding-ada-002"
)

# 새 컬렉션 생성
collection = client.create_collection(
    name=collection_name,
    embedding_function=embedding_function
)

# 엑셀 파일 로드
df = pd.read_excel(EXCEL_PATH)

# documents, metadata, ids 생성
documents = []
metadatas = []
ids = []

for idx, row in df.iterrows():
    phone_name = row['기종명']
    brand = row['브랜드']
    year = row['출시 연도']
    spec = row['기종 정보']

    # LLM에게 주고 싶은 문장 구조 (RAG 검색 기반)
    description = f"{brand}의 {phone_name}은 {year}년에 출시된 스마트폰으로, 주요 사양은 {spec}입니다."

    documents.append(description)

    metadatas.append({
        "phone_name": phone_name,
        "brand": brand,
        "year": year
    })

    ids.append(str(idx))  # 인덱스를 문자열로 변환해서 고유값 생성

# 데이터 추가
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print("최신 스마트폰 정보를 벡터DB에 성공적으로 저장했습니다!")
