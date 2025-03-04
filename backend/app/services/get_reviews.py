from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import time

def get_reviews_with_selenium(restaurant_name, restaurant_id):
    """네이버 지도에서 특정 식당의 리뷰를 크롤링"""
    try:
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # 테스트시 주석처리
        chrome_options.add_argument('--window-size=1920,1080')
        
        driver = webdriver.Chrome(options=chrome_options)
        print(f"🌐 '{restaurant_name}' 검색 중...")
        
        # 네이버 지도 검색 URL
        search_url = f"https://map.naver.com/p/search/{restaurant_name}"
        driver.get(search_url)
        time.sleep(3)
        
        try:
            search_iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#searchIframe"))
            )
            driver.switch_to.frame(search_iframe)
            print("✅ searchIframe 진입 완료")

            current_url = driver.current_url
            review_url = current_url.split("?")[0] + "?c=15.00,0,0,0,dh&placePath=/review&isCorrectAnswer=true"
            driver.get(review_url)
            time.sleep(3)
            print("✅ 리뷰 페이지 직접 이동 완료")
            
            entry_iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#entryIframe"))
            )
            driver.switch_to.frame(entry_iframe)
            print("✅ entryIframe 진입 완료")
            time.sleep(2)
        
            review_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.place_apply_pui"))
            )
            print(f"✅ {len(review_elements)}개의 리뷰 발견")
            
            if not review_elements:
                print("⚠️ 리뷰 요소를 찾을 수 없습니다. 페이지 소스 확인:")
                print(driver.page_source[:500])
            
            reviews = []
            for review_element in review_elements[:20]:
                try:
                    review_text = review_element.find_element(By.CSS_SELECTOR, "div.pui__vn15t2 a").text
                    review_data = {
                        "restaurant_id": restaurant_id,
                        "content": review_text,
                        "source": "naver_map"
                    }
                    reviews.append(review_data)
                except Exception as e:
                    print(f"리뷰 추출 실패: {str(e)}")
                    continue
            
            return reviews
        except TimeoutException as e:
            print(f"⚠️ 에러 발생: {str(e)}")
            print("현재 URL:", driver.current_url)
            return []

    except Exception as e:
        print(f"❌ {restaurant_name} 크롤링 중 오류 발생: {str(e)}")
        print("현재 URL:", driver.current_url)
        return []

    finally:
        driver.quit()

def save_reviews_to_db(supabase, reviews):
    for review in reviews:
        try:
            supabase.table("reviews").insert(review).execute()
        except Exception as e:
            print(f"❌ 리뷰 저장 실패: {str(e)}")

def main(supabase):
    response = supabase.table("restaurants").select("id, name").execute()
    restaurants = response.data
    
    for restaurant in restaurants:
        print(f"📌 {restaurant['name']}의 리뷰 수집 중...")
        reviews = get_reviews_with_selenium(restaurant['name'], restaurant['id'])
        
        if reviews:
            save_reviews_to_db(supabase, reviews)
            print(f"✅ {restaurant['name']} 리뷰 저장 완료 ({len(reviews)}개)")
        else:
            print(f"⚠️ {restaurant['name']} 리뷰 없음")

if __name__ == "__main__":
    # Supabase 연결
    load_dotenv()
    DB_URL = os.getenv("DB_URL")
    DB_KEY = os.getenv("DB_KEY")
    supabase: Client = create_client(DB_URL, DB_KEY)
    
    # 실제 리뷰 크롤링 실행
    main(supabase)

