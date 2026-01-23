import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
import requests
import time
import os


class DanawaCrawler:
    """다나와 리뷰 크롤러"""
    
    def __init__(self, output_dir='/home/lab13/airflow/data/danawa'):
        self.output_dir = output_dir
        self.driver = None
        self.wait = None
        self.df = pd.DataFrame(columns=['scoring', 'market', 'purchasing_date', 
                                        'review_title', 'review_content'])
        
        # 크롤링 대상 URL
        self.urls = [
            ['S24', 'https://search.danawa.com/dsearch.php?query=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90+%EA%B0%A4%EB%9F%AD%EC%8B%9Cs24+256gb%2C+%EC%9E%90%EA%B8%89%EC%A0%9C&originalQuery=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90+%EA%B0%A4%EB%9F%AD%EC%8B%9Cs24+256gb%2C+%EC%9E%90%EA%B8%89%EC%A0%9C&checkedInfo=N&volumeType=allvs&page=1&limit=40&sort=opinionDESC&list=list&boost=true&tab=main&addDelivery=N&coupangMemberSort=N&simpleDescOpen=Y&mode=simple&isInitTireSmartFinder=N&recommendedSort=N&defaultUICategoryCode=122515&defaultPhysicsCategoryCode=224%7C48419%7C48829%7C0&defaultVmTab=8&defaultVaTab=2041&isZeroPrice=Y&quickProductYN=N&priceUnitSort=N&priceUnitSortOrder=A'],
            ['아이폰16', 'https://search.danawa.com/dsearch.php?query=%EC%95%84%EC%9D%B4%ED%8F%B016+%EC%9E%90%EA%B8%89%EC%A0%9C'],
            ['플립6', 'https://search.danawa.com/dsearch.php?query=%EA%B0%A4%EB%9F%AD%EC%8B%9Cz%ED%94%8C%EB%A6%BD6+%EC%9E%90%EA%B8%89%EC%A0%9C'],
            ['폴드6', 'https://search.danawa.com/dsearch.php?query=%EA%B0%A4%EB%9F%AD%EC%8B%9Cz+%ED%8F%B4%EB%93%9C6']
        ]
        self.target_item = [self.urls[0][0], self.urls[1][0]]
        
        os.makedirs(self.output_dir, exist_ok=True)
    
    def setup_driver(self):
        """Selenium 드라이버 설정"""
        chrome_option = Options()
        chrome_option.add_argument('--headless')
        chrome_option.add_argument('--no-sandbox')
        chrome_option.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=chrome_option)
        self.wait = WebDriverWait(self.driver, 20)
    
    def save_to_df(self, scoring, market, purchasing_date, review_title, review_content):
        """크롤링 데이터를 DataFrame에 저장"""
        tmp_list = []
        for s, m, d, t, c in zip(scoring, market, purchasing_date, review_title, review_content):
            tmp_list.append([s, m, d, t, c])
        
        new_df = pd.DataFrame(data=tmp_list, 
                             columns=['scoring', 'market', 'purchasing_date', 
                                     'review_title', 'review_content'])
        self.df = pd.concat([self.df, new_df], ignore_index=True)
    
    def check_target_item(self, link, idx):
        """타겟 아이템 확인"""
        self.driver.get(link)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        title_elem = soup.select('#blog_content > div.summary_info > div.top_summary > h3 > span')
        
        if not title_elem:
            return None, 0
        
        title_text = title_elem[0].text
        if self.target_item[idx] in title_text:
            return title_text, 1
        return title_text, 0
    
    def crawl_page(self):
        """현재 페이지 크롤링"""
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        review_area = soup.select('#danawa-prodBlog-productOpinion-list-self > div.mall_review > div.area_right')
        
        if not review_area:
            return None, None, None, None, None
        
        scoring = [i.text for i in review_area[0].select('#danawa-prodBlog-companyReview-content-list div.top_info span.point_type_s span')]
        market = [i['alt'] for i in review_area[0].select('#danawa-prodBlog-companyReview-content-list div.top_info span.mall img')]
        purchasing_date = [i.text for i in review_area[0].select('#danawa-prodBlog-companyReview-content-list span.date')]
        review_title = [i.text for i in review_area[0].select('[id^="danawa-prodBlog-companyReview-content-wrap-"] > div.atc_cont > div.tit_W')]
        review_content = [i.text for i in review_area[0].select('div.atc')]
        
        return scoring, market, purchasing_date, review_title, review_content
    
    def crawl_all_pages(self):
        """모든 페이지 크롤링"""
        time.sleep(2)
        self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#danawa-prodBlog-productOpinion-list-self > div.mall_review > div.area_right'))
        )
        
        review_soup = BeautifulSoup(self.driver.page_source, 'html.parser').select(
            '#danawa-prodBlog-productOpinion-list-self > div.mall_review > div.area_right'
        )[0]
        
        # 페이지 리스트 추출
        self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#danawa-prodBlog-companyReview-content-list > div > div > div span'))
        )
        
        page_list = []
        page_list.append(review_soup.select('#danawa-prodBlog-companyReview-content-list > div > div > div span')[0].text)
        for a_tag in review_soup.select('#danawa-prodBlog-companyReview-content-list > div > div > div a'):
            page_list.append(a_tag['data-pagenumber'])
        
        # 각 페이지 크롤링
        for page_num in page_list:
            print(f'{page_num}페이지 크롤링 시작')
            page_num = int(page_num)
            
            if page_num % 10 >= 2:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f'a[data-pagenumber="{page_num}"]'))
                )
                time.sleep(1)
                self.driver.find_element(By.CSS_SELECTOR, f'a[data-pagenumber="{page_num}"]').click()
            
            scoring, market, purchasing_date, review_title, review_content = self.crawl_page()
            if scoring:
                self.save_to_df(scoring, market, purchasing_date, review_title, review_content)
    
    def get_product_links(self, url):
        """상품 상세 링크 추출"""
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'}
        res = requests.get(url, headers=header)
        soup = BeautifulSoup(res.text, 'html.parser')
        soup2 = soup.select('#productListArea > div.main_prodlist.main_prodlist_list > ul')
        
        if not soup2:
            return []
        
        link_list = []
        for a_tag in soup2[0].select('a', class_='click_log_prod_review_count'):
            if a_tag['href'] not in ['#', '']:
                link_list.append(a_tag['href'])
        
        # 리뷰가 있는 링크만 필터링
        return [link for link in link_list if 'companyReviewYN=Y' in link]
    
    def run(self):
        """크롤링 실행"""
        try:
            self.setup_driver()
            
            for product_info in self.urls:
                product_name = product_info[0]
                url = product_info[1]
                
                print(f'\n{product_name} 크롤링 시작')
                self.driver.get(url)
                
                self.wait.until(
                    EC.presence_of_element_located((By.ID, 'paginationArea'))
                )
                
                # 120개씩 보기
                Select(self.driver.find_element(By.CSS_SELECTOR, 
                       '#DetailSearch_Wrapper > div.view_opt > div > select')).select_by_value('120')
                
                # 상품 링크 추출
                link_list = self.get_product_links(url)
                print(f'{product_name} 상품 {len(link_list)}개 발견')
                
                # 각 상품별 리뷰 크롤링
                for idx, link in enumerate(link_list):
                    self.df = pd.DataFrame(columns=['scoring', 'market', 'purchasing_date', 
                                                   'review_title', 'review_content'])
                    
                    for target_idx in range(2):
                        item_title, is_target = self.check_target_item(link, target_idx)
                        
                        if is_target:
                            try:
                                self.crawl_all_pages()
                                self.df['item'] = item_title
                                
                                # Parquet 파일로 저장
                                output_file = os.path.join(self.output_dir, 
                                                          f'danawa_review_{product_name}_{idx}.parquet')
                                self.df.to_parquet(output_file, index=False)
                                print(f'저장 완료: {output_file}')
                            except TimeoutException:
                                print(f'{product_name} {idx}번 상품 크롤링 완료')
                                continue
            
            print('\n★ 전체 크롤링 완료 ★')
            
        except Exception as e:
            print(f'크롤링 오류 발생: {e}')
            raise
        finally:
            if self.driver:
                self.driver.quit()


def crawl_danawa():
    """Airflow Task에서 호출할 함수"""
    crawler = DanawaCrawler()
    crawler.run()


if __name__ == '__main__':
    crawl_danawa()