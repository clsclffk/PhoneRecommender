from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp
import pymysql
from airflow.models import Variable
import os


class SparkProcessor:
    """Spark를 이용한 데이터 처리 및 MySQL 적재"""
    
    def __init__(self, source='danawa'):
        self.source = source
        
        # MySQL 연결 정보
        self.mysql_ip = Variable.get('mysql_ip', default_var='15.168.221.131')
        self.user_id = Variable.get('user_id', default_var='lab13')
        self.user_password = Variable.get('user_password', default_var='lab13')
        self.database = Variable.get('mysql_DB', default_var='SNS_DB')
        
        # HDFS 경로
        self.hdfs_path = f"hdfs:///{source}_data/"
        
        # MySQL JDBC URL
        self.mysql_url = (f"jdbc:mysql://{self.mysql_ip}:3306/{self.database}"
                         "?useSSL=false&allowPublicKeyRetrieval=true"
                         "&useUnicode=true&characterEncoding=UTF-8")
        
        # MySQL 테이블명
        self.table_name = f"tbCrawled_{source.capitalize()}"
        
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
        df = self.spark.read.parquet(self.hdfs_path)
        print(f"HDFS에서 데이터 로드 완료: {df.count()}건")
        return df
    
    def preprocess_youtube_data(self, df):
        """유튜브 데이터 전처리"""
        # 시간 형식 변환
        time_cols = ['comment_publish_date', 'publish_date']
        for col_name in time_cols:
            df = df.withColumn(
                col_name,
                to_timestamp(col(col_name), "yyyy-MM-dd'T'HH:mm:ss'Z'")
            )
        
        # 결측치 처리 및 중복 제거
        df = df.fillna('MISSING')
        df = df.dropDuplicates()
        
        print(f"전처리 완료: {df.count()}건")
        return df
    
    def truncate_table(self):
        """MySQL 테이블 초기화"""
        conn = pymysql.connect(
            host=self.mysql_ip,
            user=self.user_id,
            password=self.user_password,
            database=self.database
        )
        
        cursor = conn.cursor()
        truncate_query = f"TRUNCATE TABLE {self.table_name}"
        cursor.execute(truncate_query)
        conn.commit()
        
        cursor.close()
        conn.close()
        print(f"{self.table_name} 테이블 초기화 완료")
    
    def save_to_mysql(self, df):
        """DataFrame을 MySQL에 저장"""
        df.write.format('jdbc') \
            .options(
                url=self.mysql_url,
                driver='com.mysql.jdbc.Driver',
                dbtable=self.table_name,
                user=self.user_id,
                password=self.user_password
            ) \
            .mode('append') \
            .save()
        print(f"MySQL에 데이터 적재 완료")
    
    def process(self):
        """전체 처리 프로세스 실행"""
        try:
            self.build_spark()
            df = self.load_from_hdfs()
            
            # 유튜브 데이터인 경우 전처리 추가
            if self.source == 'youtube':
                df = self.preprocess_youtube_data(df)
            
            self.truncate_table()
            self.save_to_mysql(df)
            print(f"\n★ {self.source.upper()} 데이터 처리 완료 ★")
        
        except Exception as e:
            print(f"처리 중 오류 발생: {e}")
            raise
        
        finally:
            if self.spark:
                self.spark.stop()


def process_danawa_data():
    """Airflow Task에서 호출할 함수 - 다나와"""
    processor = SparkProcessor(source='danawa')
    processor.process()


def process_youtube_data():
    """Airflow Task에서 호출할 함수 - 유튜브"""
    processor = SparkProcessor(source='youtube')
    processor.process()


if __name__ == '__main__':
    process_danawa_data()