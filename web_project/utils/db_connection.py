import json
from django.db import transaction
from hobbies.models import HobbyKeywords
from utils.llm_api import get_keyword
import mysql.connector

# MySQL 연결 함수
def get_db_connection():
    return mysql.connector.connect(
        host="15.168.221.131",
        user="lab13",
        password="lab13",
        database="SNS_DB",
        charset="utf8mb4"
    )

# 취미가 있는지 없는지 확인하고, 없으면 LLM을 호출하여 저장하는 함수
def check_hobby(hobby):
    if not hobby:
        print("[ERROR] hobby_name이 없습니다.")
        return None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 기존 취미 검색
        cursor.execute("""
            SELECT hobby_id, keyword_list FROM hobby_keywords 
            WHERE hobby_name = %s
        """, (hobby,))

        result = cursor.fetchone()

        if result:
            hobby_id, keyword_list = result
            keyword_list = json.loads(keyword_list) if keyword_list else []

            # 기존 취미지만 키워드가 없으면 LLM 호출하여 업데이트
            if not keyword_list or len(keyword_list) < 3:
                keywords = get_keyword(hobby)
                if not keywords:
                    print(f"[ERROR] '{hobby}' 키워드 생성 실패")
                    return hobby_id  # 기존 hobby_id만 리턴

                cursor.execute("UPDATE hobby_keywords SET keyword_list = %s, updated_at = NOW() WHERE hobby_id = %s", (json.dumps(keywords), hobby_id))
                conn.commit()

            return hobby_id
        
        # 기존 취미가 없다면 LLM을 호출하여 새로 저장
        keywords = get_keyword(hobby)
        if not keywords:
            print(f"[ERROR] '{hobby}' 키워드 생성 실패 → 신규 생성 중단")
            return None

        cursor.execute("INSERT INTO hobby_keywords (hobby_name, keyword_list, created_at, updated_at) VALUES (%s, %s, NOW(), NOW())", (hobby, json.dumps(keywords)))
        conn.commit()
        return cursor.lastrowid

    except Exception as e:
        print(f"[ERROR] check_hobby 오류: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


