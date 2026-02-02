from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp
from datetime import datetime
import pymysql
from airflow.models import Variable
import os

class SparkProcessor:
    """Spark를 이용한 데이터 처리 및 MySQL 적재"""
    
    def __init__(self, source='danawa', target_date=None):
        self.source = source
        # target_date가 있으면 그 날짜를 쓰고, 없으면 오늘 날짜를 기본값으로 함 
        self.target_date = target_date if target_date else datetime.now().strftime('%Y-%m-%d')
        self.today = self.target_date
        
        # Django 모델 필드에 맞춘 컬럼 매핑 정의
        if self.source == 'youtube':
            self.mapping = {
                "video_id": "video_id",
                "comment": "content",
                "like_count": "like_count",
                "comment_publish_date": "commented_at"
            }
            self.table_name = "tb_raw_youtube" # Django 테이블명
        else:
            self.mapping = {
                "item": "item_name",
                "review_content": "content",
                "scoring": "rating",
                "purchasing_date": "purchased_at"
            }
            self.table_name = "tb_raw_danawa" # Django 테이블명
            
        self.required_cols = list(self.mapping.keys())
        
        # MySQL 연결 정보
        self.mysql_ip = Variable.get('mysql_ip', default_var='15.168.221.131')
        self.user_id = Variable.get('user_id', default_var='lab13')
        self.user_password = Variable.get('user_password', default_var='lab13')
        self.database = Variable.get('mysql_DB', default_var='SNS_DB')
        
        # HDFS 경로
        self.hdfs_path = f"hdfs:///{source}_data/{self.target_date}/"
        
        # MySQL JDBC URL
        self.mysql_url = (f"jdbc:mysql://{self.mysql_ip}:3306/{self.database}"
                         "?useSSL=false&allowPublicKeyRetrieval=true"
                         "&useUnicode=true&characterEncoding=UTF-8")
        
        # Spark 설정
        os.environ['PYSPARK_SUBMIT_ARGS'] = '--jars /usr/local/lib/mysql-connector-java-5.1.49.jar pyspark-shell'
        
        self.spark = None
    
    def build_spark(self):
        """Spark 세션 생성"""
        self.spark = SparkSession.builder \
            .appName(f"{self.source.upper()} to MySQL") \
            .config("spark.hadoop.fs.defaultFS", "hdfs://localhost:9000") \
            .getOrCreate()
        print(f"Spark 세션 생성 완료")
    
    def load_from_hdfs(self):
        """HDFS에서 Parquet 파일 로드"""
        # 필요한 열만 선택적으로 읽어 I/O 효율화
        df = self.spark.read.parquet(self.hdfs_path).select(*self.required_cols)
        print(f"HDFS에서 데이터 로드 완료: {df.count()}건")
        return df
    
    def preprocess_youtube_data(self, df):
        """유튜브 데이터 전처리"""
        # Django 모델 필드명으로 변경
        for spark_col, django_col in self.mapping.items():
            df = df.withColumnRenamed(spark_col, django_col)

        # 시간 형식 변환
        time_cols = ['commented_at']
        for col_name in time_cols:
            df = df.withColumn(
                col_name,
                to_timestamp(col(col_name), "yyyy-MM-dd'T'HH:mm:ss'Z'")
            )
        
        # 결측치 처리 및 중복 제거
        df = df.fillna('MISSING', subset=['content'])
        df = df.dropDuplicates(['video_id', 'content', 'commented_at'])
        
        print(f"전처리 완료: {df.count()}건")
        return df

    def preprocess_danawa_data(self, df):
        """다나와 데이터 전처리"""
        # Django 모델 필드명으로 변경
        for spark_col, django_col in self.mapping.items():
            df = df.withColumnRenamed(spark_col, django_col)

        # 결측치 처리 및 중복 제거
        df = df.fillna('MISSING', subset=['content'])
        df = df.dropDuplicates(['item_name', 'content', 'purchased_at'])
        
        return df
    
    def save_to_mysql_with_partition(self, df):
        """날짜별 파티션 Overwrite (멱등성 확보)"""
        # 데이터 양이 적으므로 파티션을 1개로 합쳐서 계산 
        df = df.coalesce(1)
        conn = pymysql.connect(
            host=self.mysql_ip,
            user=self.user_id,
            password=self.user_password,
            database=self.database
        )
        cursor = conn.cursor()
        
        try:
            # Django 모델 필드명에 맞춰 날짜 기준 컬럼 변경
            if self.source == 'youtube':
                delete_query = f"DELETE FROM {self.table_name} WHERE DATE(commented_at) >= '{self.today}'"
            else:
                delete_query = f"DELETE FROM {self.table_name} WHERE DATE(purchased_at) >= '{self.today}'"
            
            cursor.execute(delete_query)
            conn.commit()
            print(f"파티션 삭제 완료")
            
            # 신규 데이터 적재
            df.write.format('jdbc')\
                .options(
                    url=self.mysql_url,
                    driver='com.mysql.jdbc.Driver',
                    dbtable=self.table_name,
                    user=self.user_id,
                    password=self.user_password,
                    batchsize="5000",
                    rewriteBatchedStatements="true"
                )\
                .mode('append')\
                .save()
            
            new_rows = df.count()
            print(f"파티션 적재: {self.today} 데이터 {new_rows}건 추가")
        
        except Exception as e:
            conn.rollback()
            print(f"적재 실패: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def process(self):
        """전체 처리 프로세스 실행"""
        try:
            self.build_spark()
            df = self.load_from_hdfs()
            
            if self.source == 'youtube':
                df = self.preprocess_youtube_data(df)
            else:
                df = self.preprocess_danawa_data(df)
            
            self.save_to_mysql_with_partition(df)
            print(f"\n{self.source.upper()} 데이터 처리 완료")
        
        except Exception as e:
            print(f"처리 중 오류 발생: {e}")
            raise
        finally:
            if self.spark:
                self.spark.stop()

def process_danawa_data(**kwargs):
    """Airflow Task에서 호출할 함수 - 다나와"""
    target_date = kwargs.get('ds') 
    processor = SparkProcessor(source='danawa', target_date=target_date)
    processor.process()

def process_youtube_data(**kwargs):
    """Airflow Task에서 호출할 함수 - 유튜브"""
    target_date = kwargs.get('ds')
    processor = SparkProcessor(source='youtube', target_date=target_date)
    processor.process()

if __name__ == '__main__':
    process_danawa_data()