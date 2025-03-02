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
    try:
        chrome_options = Options()
        # chrome_options.add_argument('--headless') 
        chrome_options.add_argument('--window-size=1920,1080')
        
        driver = webdriver.Chrome(options=chrome_options)
        print(f"🌐 '{restaurant_name}' 검색 중...")
        
        place_url = f"https://map.naver.com/p/entry/place/{restaurant_id}"
        driver.get(place_url)
        time.sleep(3)
        
        try:
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "entryIframe"))
            )
            
            review_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.place_section_content a[href*='review']"))
            )
            print("✅ 리뷰 탭 찾음")
            driver.execute_script("arguments[0].click();", review_tab)
            time.sleep(2)
            
            review_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.place_section.k5tcc"))
            )
            
    
            review_elements = review_container.find_elements(By.CSS_SELECTOR, "div.ZZ4OK, div._3FaRE")
            print(f"✅ {len(review_elements)}개의 리뷰 발견")
            
            reviews = []
            for review_element in review_elements[:20]:
                try:
                    review_text = review_element.find_element(
                        By.CSS_SELECTOR, 
                        "span.zPfVt, span._3l2Rq"
                    ).text
                    
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
            print(f"⚠️ {restaurant_name}: 검색 결과 또는 리뷰를 찾을 수 없습니다.")
            print("현재 URL:", driver.current_url)
            print("에러 상세:", str(e))
            return []

    except Exception as e:
        print(f"❌ {restaurant_name} 크롤링 중 오류 발생: {str(e)}")
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

def test_first_five_restaurants():
    load_dotenv()
    DB_URL = os.getenv("DB_URL")
    DB_KEY = os.getenv("DB_KEY")
    supabase: Client = create_client(DB_URL, DB_KEY)
    
    try:
        response = supabase.table("restaurants").select("id, name").limit(5).execute()
        restaurants = response.data
        
        print(f"📍 테스트할 식당 목록:")
        for i, restaurant in enumerate(restaurants, 1):
            print(f"\n{i}. {restaurant['name']}")
            print(f"🔍 리뷰 크롤링 중...")
            
            reviews = get_reviews_with_selenium(restaurant['name'], restaurant['id'])
            
            print(f"📊 검색된 리뷰 수: {len(reviews)}개")
            if reviews:
                print("📝 첫 번째 리뷰 샘플:")
                print(reviews[0]['content'][:100] + "..." if len(reviews[0]['content']) > 100 else reviews[0]['content'])
            print("-" * 50)
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    test_first_five_restaurants()
