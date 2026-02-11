from hobbies.models import TbHobbies

# MySQL 연결 함수 (레거시 호환용 - 현재는 TbHobbies ORM 사용)
def get_db_connection():
    import mysql.connector
    return mysql.connector.connect(
        host="15.168.221.131",
        user="lab13",
        password="lab13",
        database="SNS_DB",
        charset="utf8mb4"
    )

# 취미가 tb_hobbies에 있는지 확인하고, 없으면 생성 후 hobby_id 반환
def check_hobby(hobby):
    if not hobby:
        print("[ERROR] hobby_name이 없습니다.")
        return None
    try:
        obj, _ = TbHobbies.objects.get_or_create(hobby_name=hobby.strip())
        return obj.hobby_id
    except Exception as e:
        print(f"[ERROR] check_hobby 오류: {e}")
        return None
