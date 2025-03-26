from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp
import os
from dotenv import load_dotenv

import pymysql

from airflow.models import Variable
# 상위 폴더(../)에 있는 `.env` 파일 로드
#dotenv_path = os.path.abspath(os.path.join(os.getcwd(), "..", ".env"))
#load_dotenv(dotenv_path)

## mysql 연결
user_ip = Variable.get('mysql_ip', default_var = '15.168.221.131')
user_id = Variable.get('user_id', default_var = 'lab13')
user_password = Variable.get('user_password', default_var = 'lab13')
access_DATABASE = Variable.get('mysql_DB', default_var = 'SNS_DB')

os.environ['PYSPARK_SUBMIT_ARGS'] = '--jars /usr/local/lib/mysql-connector-java-5.1.49.jar pyspark-shell'

#mysql_url = f"jdbc:mysql://{os.getenv('host_ip')}:3306/{os.getenv('DATABASE')}?useSSL=false&allowPublicKeyRetrieval=true&useUnicode=true&characterEncoding=UTF-8"
mysql_url = f"jdbc:mysql://{user_ip}:3306/{access_DATABASE}?useSSL=false&allowPublicKeyRetrieval=true&useUnicode=true&characterEncoding=UTF-8"

#convert_cols = ['comment_publish_date', 'publish_date']

def build_spark():
    # SparkSession 생성
    spark = SparkSession.builder \
        .appName("HDFS to MySQL") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://localhost:9000") \
        .getOrCreate()
    return spark

def load_hdfs_files(spark):
    # HDFS에 있는 모든 Parquet 파일 로드
    df = spark.read.parquet("hdfs:///danawa_data/")
    return df

#def df_preprocessing(df, convert_cols):
#    ## 시간 형식 수정(yyyy.mm.dd HH:MM:SS)
#    for c in convert_cols:
#        df = df.withColumn(c
#                        , to_timestamp(col('comment_publish_date'), "yyyy-MM-dd'T'HH:mm:ss'Z'")
#                        )
#    ## 결측치및 중복값  제거
#    df = df.dropna().distinct()
#    print(f'''
#    결측치와 중복된 값을 모두 제거했습니다.
#    {df.count()}
#    ''')
#    return df

def truncate_table():
    # PyMySQL로 MySQL 연결 (SQL 실행을 위해)
    global user_id, user_ip, user_password, access_DATABASE
    conn = pymysql.connect(
        host=user_ip,
        user=user_id,
        password=user_password,
        database=access_DATABASE,
    )

    cursor = conn.cursor()

    # ✅ MySQL 테이블 `TRUNCATE`
    truncate_query = "TRUNCATE TABLE tbCrawled_Danawa"
    cursor.execute(truncate_query)

    conn.commit()
    cursor.close()
    conn.close()
    return print('테이블 날렸습니다.')

def save_to_sql(df):
    global user_id, user_password
    df.write.format('jdbc')\
        .options(
            url = mysql_url
            , driver = 'com.mysql.jdbc.Driver'
            , dbtable = 'tbCrawled_Danawa'
            , user = user_id
            , password = user_password
        )\
        .mode('append')\
        .save()
    return print('mysql에 데이터삽입을 완료했습니다~~!!')

def main():
    spark = build_spark()
    df = load_hdfs_files(spark)
    # df = df_preprocessing(df, convert_cols)
    truncate_table()
    save_to_sql(df)
    spark.stop()

if __name__ == '__main__':
    main()
