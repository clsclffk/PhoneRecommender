from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import chromadb
import openai
import os

client = chromadb.PersistentClient(path='/home/lab13/web_project/vector_db/analysis')

collection = client.get_or_create_collection(
    name="analysis_comments",
    embedding_function=OpenAIEmbeddingFunction(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model_name="text-embedding-ada-002"
    )
)

def search_related_sentences(query, brand=None, top_k=20):
    """
    취미(쿼리)에 대해 연관 문장 검색 (브랜드 필터 가능)
    """
    filters = {}
    if brand:
        filters['brand'] = brand

    result = collection.query(
        query_texts=[query],
        n_results=top_k,
        where=filters
    )

    # 결과에서 문장만 추출, 결과 없으면 빈 리스트 반환
    sentences = result['documents'][0] if result and result['documents'] else []

    print(f"[RAG] '{query}' → 유사 문장 검색 결과 {len(sentences)}개")
    return sentences

def extract_keywords_with_llm(sentences, top_k=20):
    api_key = os.environ.get("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=api_key)
    """
    LLM을 사용하여 중요 키워드 추출
    """
    try:
        # 리스트를 하나의 문자열로 합치기
        combined_text = "\n".join(sentences[:50])  # 너무 길면 잘라서 던짐

        system_prompt = '''
        [역할]
        너는 문서에서 가장 핵심적인 스마트폰 기능 키워드를 추출하는 역할을 하는 AI야.
        
        [기준]
        1. 사람들이 스마트폰을 사용할 때 중요하게 여기는 기능/사양/부품을 중심으로 키워드를 추출해.
        2. 각 키워드는 명사 위주의 한 단어로, 간결하고 쉬운 단어여야 해.
        3. 너무 기술적인 단어는 피하고, 사람들이 일상적으로 쓰는 단어를 선택해.
        4. 반드시 쉼표(,)로 구분해서 한 줄로만 출력해. 다른 말은 절대 하지 마.
        5. 키워드가 명백히 윤리적으로 부적절하거나, 성인 콘텐츠와 관련이 있거나, 비속어나 은어에 해당하는 경우엔 절대로 추출하지 마. 
        
        [중요도 순서]
        가장 중요한 키워드를 가장 앞에 두고, 중요도가 낮을수록 뒤에 배치해.  
        (중요도 기준: 사람들이 가장 많이 언급하고, 많이 신경 쓰는 기능/사양일수록 중요함)
        
        [예시]
        입력: 화면이 선명하고 배터리가 오래가서 좋다. 카메라 화질도 뛰어나다.
        출력: 배터리, 화면, 카메라, 화질
        '''

        user_prompt = f'''
        아래 문장들을 참고해서 중요 키워드를 {top_k}개만 뽑아줘.\n
        문장들:\n{combined_text}
        '''

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5
        )

        raw_keywords = response.choices[0].message.content.strip()

        # 쉼표로 분리
        keywords = [kw.strip() for kw in raw_keywords.split(",")]

        print(f"[LLM 키워드 추출] {keywords}")
        return keywords

    except Exception as e:
        print(f"[ERROR] 키워드 추출 실패: {e}")
        return []