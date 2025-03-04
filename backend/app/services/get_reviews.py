import hashlib
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
from app.models.review import Review

def generate_review_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

def get_reviews_with_selenium(restaurant_name: str, restaurant_id: str) -> list[Review]:
    try:
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # 테스트시 주석처리
        chrome_options.add_argument('--window-size=1920,1080')
        
        driver = webdriver.Chrome(options=chrome_options)
        print(f"🌐 '{restaurant_name}' 검색 중...")
        
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
                    # 별점 추출 시도
                    try:
                        rating_element = review_element.find_element(By.CSS_SELECTOR, "span.pui__jhpEyP")
                        rating_text = rating_element.text
                        rating = 5.0 if rating_text else None
                    except NoSuchElementException:
                        rating = None
                    
                    # Review 모델 인스턴스 생성
                    review = Review(
                        restaurant_id=restaurant_id,
                        review_text=review_text,
                        rating=rating,
                        review_hash=generate_review_hash(review_text)
                    )
                    reviews.append(review)
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

def save_reviews_to_db(supabase: Client, reviews: list[Review]):
    for review in reviews:
        try:
            existing_review = supabase.table("reviews").select("id").eq("restaurant_id", review.restaurant_id).eq("review_hash", review.review_hash).execute()

            if existing_review.data:
                print(f"⚠️ 중복 리뷰 스킵: {review.review_text[:30]}...")
                continue

            review_data = review.model_dump(exclude={'id', 'created_at'})
            review_data['restaurant_id'] = str(review_data['restaurant_id'])  
            if review_data.get('user_id'): 
                review_data['user_id'] = str(review_data['user_id'])
            
            supabase.table("reviews").insert(review_data).execute()
            print(f"✅ 리뷰 저장 완료: {review.review_text[:30]}...")
        except Exception as e:
            print(f"❌ 리뷰 저장 실패: {str(e)}")

def main(supabase: Client):
    response = supabase.table("restaurants").select("id, name").execute()
    restaurants = response.data
    
    print(f"총 {len(restaurants)}개의 레스토랑을 찾았습니다.")
    
    for i, restaurant in enumerate(restaurants, 1):
        print(f"\n[{i}/{len(restaurants)}] 📌 {restaurant['name']}의 리뷰 수집 중...")
        try:
            reviews = get_reviews_with_selenium(restaurant['name'], restaurant['id'])
            
            if reviews:
                save_reviews_to_db(supabase, reviews)
                print(f"✅ {restaurant['name']} 리뷰 저장 완료 ({len(reviews)}개)")
            else:
                print(f"⚠️ {restaurant['name']} 리뷰 없음")
        except Exception as e:
            print(f"❌ {restaurant['name']} 처리 중 오류 발생: {str(e)}")
            continue
            
        time.sleep(2)  # 각 레스토랑 사이에 잠시 대기

if __name__ == "__main__":
    load_dotenv()
    DB_URL = os.getenv("DB_URL")
    DB_KEY = os.getenv("DB_KEY")
    supabase: Client = create_client(DB_URL, DB_KEY)
    
    main(supabase)

