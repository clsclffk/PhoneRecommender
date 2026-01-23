import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import os

# Chroma 설정
CHROMA_DB_DIR = '/home/lab13/web_project/vector_db/analysis'
openai_api_key = os.environ.get("OPENAI_API_KEY")

client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# 기존 collection 생성 or 불러오기
collection = client.get_or_create_collection(
    name="analysis_comments",
    embedding_function=OpenAIEmbeddingFunction(
        api_key=openai_api_key,
        model_name="text-embedding-ada-002"
    )
)

# 댓글 벡터화
def insert_comments_into_vector_db(df_samsung, df_apple, batch_size=1000):
    documents = []
    metadatas = []
    ids = []

    idx = 0  # 고유 ID

    # 삼성 문장 추가
    for _, row in df_samsung.iterrows():
        sentence = row['sentence']
        documents.append(sentence)
        metadatas.append({"brand": "samsung"})
        ids.append(f"samsung_{idx}")
        idx += 1

    # 애플 문장 추가
    for _, row in df_apple.iterrows():
        sentence = row['sentence']
        documents.append(sentence)
        metadatas.append({"brand": "apple"})
        ids.append(f"apple_{idx}")
        idx += 1

    if not documents:
        print("[벡터DB] 추가할 문장이 없습니다. 스킵합니다!")
        return
    print(f"[벡터DB] 전체 문서 수: {len(documents)}개, 배치 크기: {batch_size}개")

    # 배치로 나눠서 추가
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i + batch_size]
        batch_metas = metadatas[i:i + batch_size]
        batch_ids = ids[i:i + batch_size]

        print(f"[벡터DB] 배치 {i // batch_size + 1}: {len(batch_docs)}개 업로드 중...")

        collection.add(
            documents=batch_docs,
            metadatas=batch_metas,
            ids=batch_ids
        )

    print(f"[벡터DB] 모든 배치 업로드 완료! 총 {len(documents)}개 문서 추가됨.")