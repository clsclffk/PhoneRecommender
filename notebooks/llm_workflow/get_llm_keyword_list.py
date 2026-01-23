
import mysql.connector
import json
import os
import openai

# OpenAI API Key 설정
api_key = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)

# MySQL 연결 설정
db_config = {
    "host": "15.168.221.131",
    "user": "lab13",
    "password": "lab13",
    "database": "SNS_DB",
    "charset": "utf8mb4"
}

# MySQL 연결 함수
def get_db_connection():
    return mysql.connector.connect(**db_config)

# 키워드 생성 함수
def get_keyword(user_input):
    try:
        system_prompt = '''
        [역할]       
        너는 사람들의 취미 영역을 듣고, 거기서 사람들이 중요하게 생각하는 스마트폰의 기능을 키워드화해서 출력해줘. 
        반드시 아래 기준을 지켜줘야 해. 

        [기준]
        1. 사용자의 취미에 중요한 스마트폰 기능/사양/부품을 추천해줘. 
        2. 5개의 키워드를 쉼표(,)로 구분해서 한 줄로만 제공해줘. 
            네가 출력하는 응답은 키워드 5개 이외의 다른 텍스트를 포함하면 절대 안 돼.
        3. 각 키워드는 한 단어고, 5글자 이내여야 해. 간결할 수록 좋아. 
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
            model="gpt-4o-mini",
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

# 취미가 있는지 없는지 확인하고, 없으면 LLM을 호출하여 저장하는 함수
def check_hobby(hobby, gender, age_group):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT hobby_id, keyword_list FROM hobby_keywords 
                WHERE hobby_name = %s AND gender = %s AND age_group = %s
            """, (hobby, gender, age_group))

            result = cursor.fetchone()

            if result:
                hobby_id, keyword_list = result
                if keyword_list:
                    keyword_list = json.loads(keyword_list)
                else:
                    keyword_list = []
                return hobby_id, keyword_list

            keyword_list = get_keyword(hobby)

            cursor.execute("""
                INSERT INTO hobby_keywords (hobby_name, gender, age_group, keyword_list) 
                VALUES (%s, %s, %s, %s)
            """, (hobby, gender, age_group, json.dumps(keyword_list)))
            conn.commit()
            new_hobby_id = cursor.lastrowid
            return new_hobby_id, keyword_list

    except Exception as e:
        print(f"오류 발생: {e}")
        return None, []
    finally:
        conn.close()
