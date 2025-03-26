import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import os
import openai
from django.utils.timezone import now
from phone_recommendations.models import PhoneRecommendations

# 환경설정
CHROMA_DB_DIR = '/home/lab13/web_project/vector_db/'
openai_api_key = os.environ.get("OPENAI_API_KEY")

# 임베딩 및 클라이언트 초기화
embedding_function = OpenAIEmbeddingFunction(api_key=openai_api_key, model_name="text-embedding-ada-002")
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# 컬렉션 가져오기
collection_name = "phone_models"
collection = chroma_client.get_or_create_collection(
    name=collection_name,
    embedding_function=embedding_function
)

# 벡터 DB를 쿼리해서 적합한 폰 정보를 가져오는 함수
def search_phone_recommendations(hobby, selected_keywords, n_results=3):
    """
    사용자의 취미와 선택한 키워드를 기반으로 스마트폰 추천 검색
    """
    if not selected_keywords or len(selected_keywords) == 0:
        raise ValueError("selected_keywords는 최소 1개 이상 필요합니다.")
    query = f"{hobby} 관련 주요 기능: {', '.join(selected_keywords)}"
    print(f"[RAG] 검색 쿼리: {query}")

    search_results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    print(f"[RAG] 검색 결과 메타데이터: {search_results['metadatas']}")

    recommendations = []
    for metadata in search_results['metadatas'][0]:
        recommendations.append({
            "phone_name": metadata['phone_name'],
            "brand": metadata['brand'],
            "year": metadata['year']
        })

    print(f"[RAG] 최종 추천 리스트: {recommendations}")
    return recommendations

# 추천 이유를 생성해주는 함수
def generate_recommendation_text(recommendations, hobby, selected_keywords, gender=None, age_group=None):
    """LLM을 사용해서 추천 이유와 추천 문구 생성"""

    print(f"[RAG] generate_recommendation_text 호출됨")
    print(f"[RAG] 추천 리스트: {recommendations}")

    if not recommendations:
        print("[ERROR] 추천 리스트가 비어있음!")
        return "추천 후보가 없습니다."


    # 추천 후보 리스트를 문자열로 변환
    phone_list_str = "\n".join([
        f"{item['phone_name']} ({item['brand']}, {item['year']})" for item in recommendations
    ])

    # 기본 사용자 정보 템플릿
    user_info = f"""
    - 취미: {hobby}
    - 중요 기능 키워드: {', '.join(selected_keywords)}
    """
    if gender and age_group:
        user_info += f"\n- 성별: {gender}\n- 연령대: {age_group}"

    prompt = f"""
    [역할]
    너는 사용자의 취미와 중요 스마트폰 기능을 종합적으로 분석해서 스마트폰을 추천하고, 추천 이유를 간단히 설명하는 AI야.

    [사용자 정보]
    {user_info}

    [추천 후보 스마트폰 목록]
    {phone_list_str}

    [추천 기준]
    1. 사용자의 취미와 중요 기능 키워드{', 성별과 연령을 종합적으로' if gender and age_group else ''} 고려하여 적절한 스마트폰 3가지를 추천할 것.
    2. 반드시 시장 조사 및 최신 스마트폰 사용 트렌드를 반영할 것.
    3. 반드시 추천 후보 스마트폰 목록 내에서만 선택하고, 목록에 없는 기종은 추천하지 말 것.
    4. 최대한 다양한 브랜드의 기종을 추천하고, 추천 목록에 삼성과 애플 각 1개 기종을 포함할 것. 
    5. 동일한 스마트폰 라인을 추천할 경우 반드시 더 최신 기종 한 개만 추천할 것 (예. 갤럭시 S23과 S24가 추천 대상일 경우 S24를 추천).
    6. 반드시 모든 추천 후보 각각에 대해 추천 이유를 취미와 중요 기능 키워드{', 성별, 연령을 종합한' if gender and age_group else ''} 한 줄 분량의 간단한 설명과 함께 제공할 것. 추천 설명은 명사로 끝나도록 작성. 
    7. 출력은 예시와 같이 모델명 - 설명 형식으로, 그 외 데이터는 출력하지 말 것. 한국에 정발된 스마트폰의 경우 브랜드와 모델명을 한국어로 제시할 것. 

    [출력예시]
    1. ASUS ROG Phone 8 Pro - 20대 남성을 위한 게임 특화 스마트폰으로, 165Hz 디스플레이와 Snapdragon 8 Gen 3로 빠른 반응속도 제공  
    2. 아이폰 15 프로 맥스 - A17 Pro 칩과 발열 제어 기능으로 20대 남성이 즐기는 고사양 게임을 원활하게 실행  
    3. 갤럭시 S24 울트라 - 고음질 음악 감상과 밝은 야간 촬영을 위한 하이엔드 성능 제공
    """

    # LLM 호출
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        generated_text = response.choices[0].message.content.strip()
        print(f"[RAG] 생성된 추천 이유: {generated_text}")
        return generated_text
    
    except Exception as e:
        print(f"LLM 추천 생성 실패: {e}")
        return "추천 이유를 생성하는데 실패했습니다."
    
def save_recommendations_to_db(hobby_entry, selected_keywords, generated_recommendation_text):
    """
    phone_recommendations 테이블에 추천 결과를 저장
    같은 취미 + 같은 기능 키워드 조합이 이미 있으면 패스!"
    """
    selected_keywords_sorted = sorted(selected_keywords)

    # 중복 데이터 체크
    exists = PhoneRecommendations.objects.filter(
        hobby_id=hobby_entry, 
        selected_keywords=selected_keywords_sorted
    ).exists()

    if exists:
        print(f"[INFO] 이미 추천 데이터가 존재합니다! hobby_id: {hobby_entry.hobby_id}, keywords: {selected_keywords_sorted}")
        return  # 저장 스킵
    
    # 추천 문구를 JSON으로 감싸기
    recommendations_json = {
        "recommendations": generated_recommendation_text
    }

    PhoneRecommendations.objects.create(
        hobby_id=hobby_entry,
        selected_keywords=selected_keywords_sorted,
        recommendations=recommendations_json, 
        created_at=now()
    )

    print(f"[INFO] 추천 결과 저장 완료! hobby_id: {hobby_entry.hobby_id}, keywords: {selected_keywords_sorted}")

