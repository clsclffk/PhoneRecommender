import os
import openai
import json
import re

# OpenAI API Key 설정!
api_key = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)

def get_keyword(user_input):  
    """
    OpenAI GPT API를 이용해 취미 관련 키워드를 생성하는 함수
    """
    try:
        system_prompt = '''
        [역할]       
        너는 사람들의 취미 영역을 듣고, 거기서 사람들이 중요하게 생각하는 스마트폰의 기능을 키워드화해서 출력해줘. 
        반드시 아래 기준을 지켜줘야 해. 

        [기준]
        1. 사용자의 취미에 중요한 스마트폰 기능/사양/부품을 추천해줘. 
        2. 5개의 키워드를 쉼표(,)로 구분해서 한 줄로만 제공해줘. 
            네가 출력하는 응답은 키워드 5개 이외의 다른 텍스트를 포함하면 절대 안 돼.
        3. 각 키워드는 한 단어로, 5글자를 넘지 않아야 해. 간결할 수록 좋아. 
        4. 키워드는 사람들이 일상에서 많이 사용하는 쉬운 단어를 선택해. 
        5. 너무 기술적이거나 긴 단어는 피해줘(예. '스타일러스', '조리개', '이퀄라이저' 제외).  
        6. 입력된 키워드가 윤리적이지 않거나 청소년에게 적절하지 않을 경우 '입력할 수 없는 단어입니다'라고 말해줘. 
        7. 위의 사항들을 꼭 지켜서 알려줘. 

        [예시]
        사용자 입력 : '사진 촬영'
        
        원하는 결과 : '배터리', '사이즈', '화질', '용량', '초점'
        '''

        user_prompt = f'"{user_input}"과 관련된 스마트폰 기능 키워드 5개를 알려줘.'

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )

        raw_output = response.choices[0].message.content.strip()
        raw_output = raw_output.replace("'", "").split(",")
        return [res.strip() for res in raw_output]

    except Exception as e:
        print(f"오류 발생: {e}")
        return []
    
def summarize_sentences_with_llm(top_comments):
    """
    키워드별로 브랜드의 긍/부정 문장을 순화/요약하여 반환
    """
    try:
        system_prompt = '''
        [역할]
        너는 사람들이 남긴 제품 리뷰 문장을 순화하고 요약 및 정리하는 역할이야.

        [규칙]
        1. 입력된 문장을 자연스럽고 긍정/부정에 맞게 간결하게 순화해.
        2. 긍정일 경우에는 명확하게 좋은 인상을 주는 문장으로 정리해.
        3. 부정일 경우엔 너무 강한 부정은 피하고 최대한 부드럽고 완곡하게 표현해.
        4. 20자 이내로 간결하게 정리하되, 긍정/부정 요인에 대해서는 명확히 알려줘.
        5. 긍정 의견과 부정 의견이 동일한 내용에 대한 완전히 상반된 의견이어선 안돼.(예. 배터리가 충분해요/배터리가 부족해요)
            만약 요약 결과가 완전히 상반된다면, 해당 의견에 대한 구체적인 설명을 함께 서술해.(예. 일상생활에서 배터리가 충분해요/게임할 때 배터리가 부족해요)
        6. 제품 브랜드(삼성, 애플)는 언급해도 되지만, **구체적인 모델명(예: 갤럭시 S24, 아이폰 15 등)은 절대 언급하지 말 것.**
        7. 결과는 예시 형식처럼 JSON으로만 제공해. (다른 텍스트 출력 금지)

        [예시 출력 형식]
        {
            "apple": {
                "카메라": {"pos": "화질이 선명해요.", "neg": "저조도에서 아쉬워요."},
                "배터리": {"pos": "오래가요.", "neg": "충전이 느려요."}
            },
            "samsung": {
                "카메라": {"pos": "선명하고 깔끔해요.", "neg": "어두운 곳에서 흐릿해요."},
                "배터리": {"pos": "오래가요.", "neg": "충전 속도가 느려요."}
            }
        }
        '''

        # 동적 유저 프롬프트 생성
        user_prompt = "아래는 브랜드별 키워드별 대표 문장이야. 규칙에 따라 정리해줘.\n\n"

        for brand in top_comments.keys():
            user_prompt += f"{brand.upper()} 브랜드 리뷰\n"
            for keyword, sentiments in top_comments[brand].items():
                user_prompt += f"- 키워드 [{keyword}]:\n"
                user_prompt += f"  - 긍정 문장: {sentiments.get('pos', '없음')}\n"
                user_prompt += f"  - 부정 문장: {sentiments.get('neg', '없음')}\n"
            user_prompt += "\n"

        # OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5
        )

        # 응답 처리
        raw_output = response.choices[0].message.content.strip()

        clean_output = raw_output.strip('`').strip()
        if clean_output.startswith("json"):
            clean_output = clean_output[4:].strip()

        import json
        try:
            summary_result = json.loads(clean_output)
        except json.JSONDecodeError:
            print("[WARNING] LLM 응답 JSON 파싱 실패!")
            print("응답 내용:", clean_output)
            summary_result = {}

        return summary_result

    except Exception as e:
        print(f"오류 발생: {e}")
        return {}

def generate_summary_for_page_1_1(
    hobby,
    keyword_list,
    freq_apple_ratio,
    freq_samsung_ratio
):
    """페이지 1-1 요약 생성 함수 (키워드 빈도 비율)"""

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # JSON 변환
    freq_apple_ratio_json = json.dumps(freq_apple_ratio, ensure_ascii=False)
    freq_samsung_ratio_json = json.dumps(freq_samsung_ratio, ensure_ascii=False)

    prompt = f"""
    [역할]
    너는 사용자의 취미와 관련된 스마트폰 기능 키워드에 대한 키워드 빈도 분석 결과를 설명하는 AI야.

    [사용자 정보]
    - 취미: {hobby}
    - 주요 기능 키워드: {', '.join(keyword_list)}

    [분석 데이터]
    - 삼성: {freq_samsung_ratio_json}
    - 애플: {freq_apple_ratio_json}

    [조건]
    1. 분석 결과를 2~3문장으로 설명해줘.
    2. 브랜드 비교와 수치(퍼센트, 소숫점 첫째자리까지)를 포함해서 작성해줘.
    3. 아래 보고서 예시 참고해서 친근하고 발랄하게 말해줘.
    4. 문장마다 줄바꿈을 꼭 넣어줘. (한 문장 끝나면 Enter로 줄을 바꿔서 작성해줘!)
    5. 반드시 삼성에 대한 내용을 먼저, 애플에 대한 내용을 그 다음에 언급해줘. 브랜드명은 한국어로 작성해. 
    
    [보고서 예시]
    사진 촬영 취미와 관련해, SNS 이용자들은 '카메라' 키워드에 대해 가장 큰 관심을 보였어요.
    OO 브랜드에서는 45.3%, XX 브랜드에서는 38.7%로 나타났답니다.
    두 브랜드에서 가장 큰 차이를 보인 키워드는 '배터리'로, 언급량 차이가 15%였어요.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 분석 결과를 설명하는 AI야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )

        generated_summary = response.choices[0].message.content.strip()
        print("[DONE] 페이지 1-1 요약 생성 완료!")
        return generated_summary

    except Exception as e:
        print(f"[ERROR] 페이지 1-1 요약 실패: {e}")
        return "페이지 1-1 요약 생성 실패"

def generate_summary_for_page_1_2(
    hobby,
    keyword_list,
    keyword_monthly_trend
):
    """페이지 1-2 요약 생성 함수 (월별 트렌드 분석)"""

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    keyword_monthly_trend_json = json.dumps(keyword_monthly_trend, ensure_ascii=False)

    prompt = f"""
    [역할]
    너는 사용자의 취미와 관련된 스마트폰 기능 키워드의 월별 트렌드 분석 결과를 설명하는 AI야.

    [사용자 정보]
    - 취미: {hobby}
    - 주요 기능 키워드: {', '.join(keyword_list)}

    [분석 데이터]
    - 월별 트렌드: {keyword_monthly_trend_json}의 월별 언급비율('ratio') 중 최근 6개월 데이터
    ({keyword_monthly_trend_json}의 'pos_ratio', 'neg_ratio'는 사용하지 않음)

    [조건]
    1. 월별 데이터에서 최근 6개월 트렌드나 특이점을 설명해줘.
    2. 2~3문장으로 친근하고 발랄하게 써줘.
    3. 문장마다 줄바꿈을 꼭 넣어줘. (한 문장 끝나면 Enter로 줄을 바꿔서 작성해줘!)
    4. 반드시 삼성에 대한 내용을 먼저, 애플에 대한 내용을 그 다음에 언급해줘. 브랜드명은 한국어로 작성해.
    5. 해석 시 언급 비율의 변화와 관심도 변화에만 초점을 맞춰서 해석해. 
    6. 긍정/부정 비율 데이터는 절대로 사용하지 말고, 해석 내용에도 포함하지 마. 
    
    [보고서 예시]
    OO 브랜드는 '카메라' 키워드가 2024년 12월에 급상승했어요!
    반면 XX 브랜드는 '배터리' 키워드가 꾸준히 인기가 높았답니다.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 분석 결과를 설명하는 AI야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )

        generated_summary = response.choices[0].message.content.strip()
        print("[DONE] 페이지 1-2 요약 생성 완료!")
        return generated_summary

    except Exception as e:
        print(f"[ERROR] 페이지 1-2 요약 실패: {e}")
        return "페이지 1-2 요약 생성 실패"

def generate_summary_for_page_2_1(
    hobby,
    keyword_list,
    sentiment_apple_score,
    sentiment_samsung_score,
    sentiment_apple_ratio,
    sentiment_samsung_ratio,
    keyword_monthly_trend
):
    """페이지 2-1용 요약 생성 함수"""

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # JSON 변환
    sentiment_apple_score_json = json.dumps(sentiment_apple_score, ensure_ascii=False)
    sentiment_samsung_score_json = json.dumps(sentiment_samsung_score, ensure_ascii=False)
    sentiment_apple_ratio_json = json.dumps(sentiment_apple_ratio, ensure_ascii=False)
    sentiment_samsung_ratio_json = json.dumps(sentiment_samsung_ratio, ensure_ascii=False)
    keyword_monthly_trend_json = json.dumps(keyword_monthly_trend, ensure_ascii=False)
    
    prompt = f"""
    [역할]
    너는 사용자의 취미와 관련된 스마트폰 기능 키워드를 중심으로, 분석 결과를 쉽게 설명하는 AI야.

    [사용자 정보]
    - 취미: {hobby}
    - 주요 기능 키워드: {', '.join(keyword_list)}

    [분석 데이터]
    - 브랜드별 감성 점수 및 긍/부정 비율
      - 삼성 긍/부정 비율: {sentiment_samsung_ratio_json}
      - 애플 긍/부정 비율: {sentiment_apple_ratio_json}
      - 월별 감성 비율: {keyword_monthly_trend_json}의 월별 긍부정비율('pos_ratio', 'neg_ratio') 중 최근 6개월 데이터

    [조건]
    1. 이 데이터는 모델2-1 결과야!
    2. 브랜드별 긍/부정 비율(퍼센트, 소숫점 첫째자리까지)을 비교하고, 어느 브랜드가 긍정적인지 알려줘.
    3. 2~3문장으로 설명하고, 친근하고 발랄한 말투로 작성해줘.
    4. 문장마다 줄바꿈을 꼭 넣어줘. (한 문장 끝나면 Enter로 줄을 바꿔서 작성해줘!)
    5. 반드시 삼성에 대한 내용을 먼저, 애플에 대한 내용을 그 다음에 언급해줘. 브랜드명은 한국어로 작성해.
    6. 전체 기간에 대한 종합 해석을 먼저 하고, 다음에 월별 데이터에서 눈에 띄는 정보를 해석해. 
        월별 데이터는 반드시 최근 6개월에 대해서만 해석하고, 두 가지 이상 시점에 대한 설명을 할 때 최신 데이터를 먼저 설명해.
    7. 긍정/부정 비율 중 한 가지가 60% 이상인 비율일 때 긍정적/부정적이라는 해석을 해줘. 50%는 중립적이야. 
    
    [예시]
    사진 촬영 취미와 관련해, SNS 이용자들은 전체 기간동안 OO보다 XX에서 좀 더 긍정적인 반응을 보였어요.
    자세히 살펴보면, OO에서는 XXXX년 XX월에 'ee'에 대한 긍정 리뷰가 00%로 더 높았답니다.
    XXXX년 XX월에는 XX에서 'dd' 키워드에 대한 긍정적인 의견이 급상승한 게 눈에 띄네요!  
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 분석 결과를 설명하는 AI야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )

        generated_summary = response.choices[0].message.content.strip()
        print("[DONE] 페이지 2-1 요약 생성 완료!")
        return generated_summary

    except Exception as e:
        print(f"[ERROR] 페이지 2-1 요약 실패: {e}")
        return "페이지 2-1 요약 생성 실패"

def generate_summary_for_page_2_2(
    hobby,
    keyword_list,
    sentiment_top_sentences
):
    """페이지 2-2용 요약 생성 함수"""

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # JSON 변환
    sentiment_top_sentences_json = json.dumps(sentiment_top_sentences, ensure_ascii=False)

    prompt = f"""
    [역할]
    너는 사용자의 취미와 관련된 스마트폰 기능 키워드를 중심으로, SNS 의견 데이터를 분석하고 요약하는 AI야.

    [사용자 정보]
    - 취미: {hobby}
    - 주요 기능 키워드: {', '.join(keyword_list)}

    [분석 데이터]
    - SNS 긍/부정 대표 문장 요약:
      - {sentiment_top_sentences_json}

    [조건]
    1. 이 데이터는 모델2-2 결과야!
    2. SNS 유저들이 브랜드별로 어떤 긍정/부정 평가를 했는지 간결하게 정리해줘.
    3. 2~3문장으로 작성하고, 친근하고 발랄한 말투로 작성해줘.
    4. 문장마다 줄바꿈을 꼭 넣어줘. (한 문장 끝나면 Enter로 줄을 바꿔서 작성해줘!)
    5. 반드시 삼성에 대한 내용을 먼저, 애플에 대한 내용을 그 다음에 언급해줘. 브랜드명은 한국어로 작성해. 

    [예시]
    SNS 유저들은 OO 브랜드에 대해 'xx'가 좋고 'cc'가 만족스럽지만, 'oo'는 아쉽다는 의견을 보여줬어요.
    XX 브랜드는 'gg'와 'bb'가 만족스럽다는 평가를 받았지만 'ww'에서는 아쉬움이 많았답니다.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 분석 결과를 설명하는 AI야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )

        generated_summary = response.choices[0].message.content.strip()
        print("[DONE] 페이지 2-2 요약 생성 완료!")
        return generated_summary

    except Exception as e:
        print(f"[ERROR] 페이지 2-2 요약 실패: {e}")
        return "페이지 2-2 요약 생성 실패"


def generate_summary_for_page_3(
    hobby,
    keyword_list,
    related_words_apple,
    related_words_samsung
):
    """페이지 3용 요약 생성 함수"""

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    related_words_apple_json = json.dumps(related_words_apple, ensure_ascii=False)
    related_words_samsung_json = json.dumps(related_words_samsung, ensure_ascii=False)

    prompt = f"""
    [역할]
    너는 사용자의 취미와 관련된 스마트폰 기능 키워드를 중심으로, 분석 결과를 이해하기 쉽게 설명하는 AI야.

    [사용자 정보]
    - 취미: {hobby}
    - 주요 기능 키워드: {', '.join(keyword_list)}

    [연관어 분석 데이터]
    - 삼성 브랜드 연관어: {related_words_samsung_json}
    - 애플 브랜드 연관어: {related_words_apple_json}

    [조건]
    1. 모델3 결과를 2~3문장으로 설명해줘.
    2. 아래 보고서 예시처럼 친근하고 이해하기 쉽게 작성해줘.
    3. 문장마다 줄바꿈을 꼭 넣어줘. (한 문장 끝나면 Enter로 줄을 바꿔서 작성해줘!)
    4. 반드시 삼성에 대한 내용을 먼저, 애플에 대한 내용을 그 다음에 언급해줘. 브랜드명은 한국어로 작성해.
    5. 연관어에 대한 설명을 마친 후, 취미 영역과 키워드를 종합해 정리하는 문구를 보고서 예시처럼 넣어줘. 
    6. 반드시 모델3 결과만 작성하고 줄바꿈을 잘 넣어 가독성을 높여줘.

    [보고서 예시]
    연관어 분석은 이용자님의 취미와 함께 언급된 단어들에 대한 정보를 보여줘요.  
    사진 촬영 취미와 관련해 OO 브랜드에서는 'NN', 'MM', 'gg' 와 같은 단어들이 자주 등장했어요.  
    한편, XX 브랜드에서는 'NN'과 'MM' 외에도 'PP', 'QQ' 등의 단어가 자주 등장한 점에서 차이가 있네요.

    정리하면, kk 취미에서는 oo, xx 등의 기능을 주목할만 하답니다.
    새로운 스마트폰을 구매하실 땐 이런 기능들에 집중해서 골라보시면 어떨까요?
    
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 분석 결과를 설명하는 AI야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )

        generated_summary = response.choices[0].message.content.strip()

        # "정리하면" 부분 앞에 줄바꿈 추가
        generated_summary = generated_summary.replace("정리하면,", "\n정리하면,")
        
        print("[DONE] 페이지 3 요약 생성 완료!")
        return generated_summary

    except Exception as e:
        print(f"[ERROR] 페이지 3 요약 실패: {e}")
        return "페이지 3 요약 생성 실패"

