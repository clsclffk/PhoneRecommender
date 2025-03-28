import pandas as pd

from bs4 import BeautifulSoup

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException


import requests

import time

chrome_option = Options()
chrome_option.add_experimental_option('detach', True)
driver = webdriver.Chrome(options=chrome_option)
wait = WebDriverWait(driver,20)

urls = [['S24', 'https://search.danawa.com/dsearch.php?query=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90+%EA%B0%A4%EB%9F%AD%EC%8B%9Cs24+256gb%2C+%EC%9E%90%EA%B8%89%EC%A0%9C&originalQuery=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90+%EA%B0%A4%EB%9F%AD%EC%8B%9Cs24+256gb%2C+%EC%9E%90%EA%B8%89%EC%A0%9C&checkedInfo=N&volumeType=allvs&page=1&limit=40&sort=opinionDESC&list=list&boost=true&tab=main&addDelivery=N&coupangMemberSort=N&simpleDescOpen=Y&mode=simple&isInitTireSmartFinder=N&recommendedSort=N&defaultUICategoryCode=122515&defaultPhysicsCategoryCode=224%7C48419%7C48829%7C0&defaultVmTab=8&defaultVaTab=2041&isZeroPrice=Y&quickProductYN=N&priceUnitSort=N&priceUnitSortOrder=A']
       , ['아이폰16', 'https://search.danawa.com/dsearch.php?query=%EC%95%84%EC%9D%B4%ED%8F%B016+%EC%9E%90%EA%B8%89%EC%A0%9C']
       , ['플립6', 'https://search.danawa.com/dsearch.php?query=%EA%B0%A4%EB%9F%AD%EC%8B%9Cz%ED%94%8C%EB%A6%BD6+%EC%9E%90%EA%B8%89%EC%A0%9C']
       , ['폴드6', 'https://search.danawa.com/dsearch.php?query=%EA%B0%A4%EB%9F%AD%EC%8B%9Cz+%ED%8F%B4%EB%93%9C6']]

target_item = [urls[0][0], urls[1][0]]
df = pd.DataFrame(columns=['scoring', 'market', 'purchasing_date', 'review_title', 'review_content'])


def save_to_df(tmp_scoring, tmp_market, tmp_purchasing_date, tmp_review_title, tmp_review_content):
    global df
    tmp_list = []
    for s, m, d, t, c in zip(tmp_scoring, tmp_market, tmp_purchasing_date, tmp_review_title, tmp_review_content):
        tmp_list.append([s, m, d, t, c])
        
    df = pd.concat([df, pd.DataFrame(data = tmp_list, columns = ['scoring', 'market', 'purchasing_date', 'review_title', 'review_content'])])

    print('df에 저장완료!')
    return df

def click_link(link, idx):
    idx = int(idx)
    global target_item
    driver.get(link)
    tmp = BeautifulSoup(driver.page_source, 'html.parser')
    tmp_title = tmp.select('#blog_content > div.summary_info > div.top_summary > h3 > span')[0]
    if target_item[idx] in tmp_title.text:
        return tmp_title.text, 1
    
    else:
        print('hmm this is error')
        return tmp_title.text, 0



# 페이지 리스트 계산
def calc_page_list(review_soup):
    global wait
    page_list = []
    wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#danawa-prodBlog-companyReview-content-list > div > div > div span'))
    )
    
    page_list.append(review_soup.select('#danawa-prodBlog-companyReview-content-list > div > div > div span')[0].text)
    for i in review_soup.select('#danawa-prodBlog-companyReview-content-list > div > div > div a'):
        page_list.append(i['data-pagenumber'])
    return page_list


# 다음 버튼 유무
def is_click_next_button(page_list) :
    if int(page_list[0]) + 9 == int(page_list[-1]):
        return 1

    else:
        return 0
    
# 해당 페이지 크롤링
def crawling(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    review_soup = soup.select('#danawa-prodBlog-productOpinion-list-self > div.mall_review > div.area_right')
    scoring = [i.text for i in review_soup[0].select('#danawa-prodBlog-companyReview-content-list div.top_info span.point_type_s span')]
    market = [i['alt'] for i in review_soup[0].select('#danawa-prodBlog-companyReview-content-list div.top_info span.mall img')]
    purchasing_date = [i.text for i in review_soup[0].select('#danawa-prodBlog-companyReview-content-list span.date')]
    review_title = [i.text for i in review_soup[0].select('[id^="danawa-prodBlog-companyReview-content-wrap-"] > div.atc_cont > div.tit_W')]
    review_content = [i.text for i in review_soup[0].select('div.atc')]

    return scoring, market, purchasing_date, review_title, review_content


def repit_page(isTarget): 

    if isTarget == 1:
        try :
            while True:
                time.sleep(2)
                wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '#danawa-prodBlog-productOpinion-list-self > div.mall_review > div.area_right'))
                )
                review_soup = BeautifulSoup(driver.page_source, 'html.parser').select('#danawa-prodBlog-productOpinion-list-self > div.mall_review > div.area_right')[0]
                
                page_list = calc_page_list(review_soup)
                print(page_list)
                if len(page_list) == 1:
                    print(f'{page_list[0]}페이지 시작합니다~~')
                    tmp_scoring, tmp_market, tmp_purchasing_date, tmp_review_title, tmp_review_content = crawling(driver)
                    save_to_df(tmp_scoring, tmp_market, tmp_purchasing_date, tmp_review_title, tmp_review_content)
                    break
                else:
                    for i in page_list:
                        print(f'{i}페이지 시작합니다.')
                        i = int(i)
                        if i % 10 == 1:
                            tmp_scoring, tmp_market, tmp_purchasing_date, tmp_review_title, tmp_review_content = crawling(driver)
                            save_to_df(tmp_scoring, tmp_market, tmp_purchasing_date, tmp_review_title, tmp_review_content)
                            #df_to_file(df)

                        elif i % 10 >= 2:
                            
                            wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, f'a[data-pagenumber="{i}"]'))
                            )
                            time.sleep(1)
                            driver.find_element(By.CSS_SELECTOR, f'a[data-pagenumber="{i}"]').click()
                            tmp_scoring, tmp_market, tmp_purchasing_date, tmp_review_title, tmp_review_content = crawling(driver)
                            save_to_df(tmp_scoring, tmp_market, tmp_purchasing_date, tmp_review_title, tmp_review_content)
                            #df_to_file(df)

                        elif i % 10 == 0:
                            wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, f'a[data-pagenumber="{i}"]'))
                            )
                            time.sleep(1)
                            driver.find_element(By.CSS_SELECTOR, f'a[data-pagenumber="{i}"]').click()

                            tmp_scoring, tmp_market, tmp_purchasing_date, tmp_review_title, tmp_review_content = crawling(driver)
                            save_to_df(tmp_scoring, tmp_market, tmp_purchasing_date, tmp_review_title, tmp_review_content)
                            #df_to_file(df)
                            
                            wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '[id^="danawa-pagination-button-next-"] > span'))
                            )
                            driver.find_element(By.CSS_SELECTOR, '[id^="danawa-pagination-button-next-"] > span').click()

                            print('클릭함')
                    
                            print(df.tail(5))
                    
                    if not driver.find_elements(By.CSS_SELECTOR, '[id^="danawa-pagination-button-next-"] > span'):        
                        for i in page_list:
                            print(f'{i}페이지 시작합니다~~')
                            i = int(i)
                            if i % 10 == 1:
                                tmp_scoring, tmp_market, tmp_purchasing_date, tmp_review_title, tmp_review_content = crawling(driver)
                                save_to_df(tmp_scoring, tmp_market, tmp_purchasing_date, tmp_review_title, tmp_review_content)
                                #df_to_file(df)

                            elif i % 10 >= 2:
                                
                                wait.until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, f'a[data-pagenumber="{i}"]'))
                                )
                                time.sleep(1)
                                driver.find_element(By.CSS_SELECTOR, f'a[data-pagenumber="{i}"]').click()
                                tmp_scoring, tmp_market, tmp_purchasing_date, tmp_review_title, tmp_review_content = crawling(driver)
                                save_to_df(tmp_scoring, tmp_market, tmp_purchasing_date, tmp_review_title, tmp_review_content)
                                #df_to_file(df)
                            print("마지막 페이지 이제 시작합니다.")
                            break           

        except TimeoutException as e:
            print(f'{e}모든 페이지가 끝났습니다.')
    else:
        print('target이 아니라서 크롤링하지 않습니다.')

def main():
    try:
        for url in urls:
            tmp = url
            url = url[-1]
            driver.get(url)
            print(url)
            wait.until(
                EC.presence_of_element_located((By.ID, 'paginationArea'))
            )
            
            # 120개 보기로 바꿈
            Select(driver.find_element(by = By.CSS_SELECTOR, value = '#DetailSearch_Wrapper > div.view_opt > div > select')).select_by_value('120')

            header = {'User-Agent': 'Mozila/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'}
            res = requests.get(url, headers= header)
            soup = BeautifulSoup(res.text, 'html.parser')
            soup2 = soup.select('#productListArea > div.main_prodlist.main_prodlist_list > ul')
            link_list = []

            print('세부 link_list를 추출합니다. 좀 오래 걸리네요(갤럭시 1~2분, 애플 3~5분)')
            for i in range(0, len(soup2[0].select('a', class_ = 'click_log_prod_review_count'))):
                if soup2[0].select('a', class_ = 'click_log_prod_review_count')[i]['href'] != '#' or soup2[0].select('a', class_ = 'click_log_prod_review_count')[i]['href'] != '':
                    link_list.append(soup2[0].select('a', class_ = 'click_log_prod_review_count')[i]['href'])

            # 최종 리스트
            link_list = [link for link in link_list if 'companyReviewYN=Y' in link]

            print(f'''
                ▶ {url}의 세부 link_list는 다음과 같고 하나씩 추출합니다.
                ▶ {len(link_list)}개를 추출합니다.
                ▶ {link_list}
                ''')
            

            for idx, link in enumerate(link_list):
                for i in range(0, 2):
                    df = pd.DataFrame(columns = ['scoring', 'market', 'purchasing_date', 'review_title', 'review_content'])
                    item, isTarget = click_link(link, i)
                    repit_page(isTarget)
                    
                    if isTarget == 1:
                        df['item'] = item
                        df.to_parquet(f'danawa_review_{tmp[0]}+{idx}.parquet', index = False)
                        #df.to_csv(f'danawa_review_{tmp[0]}+{idx}.csv', encoding='utf-8 sig', mode = 'w', index = False, header=True)

                    else:
                        print('target item이 아니라, parquet 저장도 하지 않습니다.')
        print('★★★★★★★★★★★★★★★★★')
        print('★★★추출 끝!★★★★★★★★')
        print('★★★★★★★★★★★★★★★★★')
        driver.close()

    except ElementClickInterceptedException as e:
        print('음 ElementClickInterceptedException 에러 발생했네요 크롬창을 건들이지 마세요')
        for url in urls:
            tmp = url
            url = url[-1]
            driver.get(url)

            wait.until(
                EC.presence_of_element_located((By.ID, 'paginationArea'))
            )
            
            # 120개 보기로 바꿈
            Select(driver.find_element(by = By.CSS_SELECTOR, value = '#DetailSearch_Wrapper > div.view_opt > div > select')).select_by_value('120')

            header = {'User-Agent': 'Mozila/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'}
            res = requests.get(url, headers= header)
            soup = BeautifulSoup(res.text, 'html.parser')
            soup2 = soup.select('#productListArea > div.main_prodlist.main_prodlist_list > ul')
            link_list = []

            print('세부 link_list를 추출합니다. 좀 오래 걸리네요(갤럭시 1~2분, 애플 3~5분)')
            for i in range(0, len(soup2[0].select('a', class_ = 'click_log_prod_review_count'))):
                if soup2[0].select('a', class_ = 'click_log_prod_review_count')[i]['href'] != '#' or soup2[0].select('a', class_ = 'click_log_prod_review_count')[i]['href'] != '':
                    link_list.append(soup2[0].select('a', class_ = 'click_log_prod_review_count')[i]['href'])

            # 최종 리스트
            link_list = [link for link in link_list if 'companyReviewYN=Y' in link]

            print(f'''
                ▶ {url}의 세부 link_list는 다음과 같고 하나씩 추출합니다.
                ▶ {len(link_list)}개를 추출합니다.
                ▶ {link_list}
                ''')
            

            for idx, link in enumerate(link_list):
                for i in range(0, 2):
                    df = pd.DataFrame(columns = ['scoring', 'market', 'purchasing_date', 'review_title', 'review_content'])
                    item, isTarget = click_link(link, i)
                    repit_page(isTarget)
                    
                    if isTarget == 1:
                        df['item'] = item
                        df.to_parquet(f'danawa_review_{tmp[0]}+{idx}.parquet', index = False)
                        #df.to_csv(f'danawa_review_{tmp[0]}+{idx}.csv', encoding='utf-8 sig', mode = 'w', index = False, header=True)

                    else:
                        print('target item이 아니라, parquet 저장도 하지 않습니다.')
        print('★★★★★★★★★★★★★★★★★')
        print('★★★추출 끝!★★★★★★★★')
        print('★★★★★★★★★★★★★★★★★')
        driver.close()

if __name__ == '__main__':
    main()