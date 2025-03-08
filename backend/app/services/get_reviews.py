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


def get_reviews_with_selenium(restaurant_name: str, restaurant_id: str, district: str) -> list[Review]:
    try:
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # 테스트시 주석처리
        chrome_options.add_argument('--window-size=1920,1080')
        
        driver = webdriver.Chrome(options=chrome_options)
        print(f"🌐 '{restaurant_name}' 검색 중... (지역: {district})")
        
        search_url = f"https://map.naver.com/p/search/{restaurant_name}"
        driver.get(search_url)
        time.sleep(3)
        
        try:
            search_iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#searchIframe"))
            )
            driver.switch_to.frame(search_iframe)
            print("✅ searchIframe 진입 완료")

            try:
            
                current_url = driver.current_url
                review_url = current_url.split("?")[0] + "?c=15.00,0,0,0,dh&placePath=/review&isCorrectAnswer=true"
                driver.get(review_url)
                time.sleep(3)
                
                entry_iframe = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#entryIframe"))
                )
                print("✅ 기존 방식으로 리뷰 페이지 이동 성공")
                
            except TimeoutException:
                print("⚠️ 기존 방식 실패, district 매칭 시도...")
                
                driver.get(search_url) 
                time.sleep(3)
                
                driver.switch_to.default_content()
                search_iframe = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#searchIframe"))
                )
                driver.switch_to.frame(search_iframe)
                
                results = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.VLTHu"))
                )
                
                target_element = None
                for result in results[:5]:
                    try:
                        address = result.find_element(By.CSS_SELECTOR, "span.Pb4bU").text
                        title = result.find_element(By.CSS_SELECTOR, "span.YwYLL").text
                        
                        print(f"검색 결과: {title} / 주소: {address}")
                        
                        
                        if any(part in address for part in district.split()):
                            print(f"✅ District 매칭 성공: {title} ({address})")
                        
                            title_element = result.find_element(By.CSS_SELECTOR, "span.YwYLL")
                            title_element.click()
                            time.sleep(3)
                            target_element = result
                            break
                    except NoSuchElementException as e:
                        print(f"요소를 찾을 수 없음: {str(e)}")
                        continue
                
                if not target_element:
                    print("⚠️ 적절한 매장을 찾을 수 없습니다.")
                    return []
                
                driver.switch_to.default_content()
                entry_iframe = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#entryIframe"))
                )
                driver.switch_to.frame(entry_iframe)
                print("✅ entryIframe 진입 완료")
                
                try:
                    review_tab = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='review']"))
                    )
                    review_tab.click()
                    time.sleep(3)
                    print("✅ 리뷰 탭 클릭 완료")
                except TimeoutException:
                    print("⚠️ 리뷰 탭을 찾을 수 없습니다.")
                    return []
            
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
                    try:
                        rating_element = review_element.find_element(By.CSS_SELECTOR, "span.pui__jhpEyP")
                        rating_text = rating_element.text
                        rating = 5.0 if rating_text else None
                    except NoSuchElementException:
                        rating = None
                    
                
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
    response = supabase.table("restaurants").select("id, name, district").execute()
    restaurants = response.data
    
    print(f"총 {len(restaurants)}개의 레스토랑을 찾았습니다.")
    
    for i, restaurant in enumerate(restaurants, 1):
        try:
            existing_reviews = supabase.table("reviews").select("id").eq("restaurant_id", restaurant['id']).execute()
            
            if existing_reviews.data:
                print(f"\n[{i}/{len(restaurants)}] 📌 {restaurant['name']}의 리뷰가 이미 존재합니다. 스킵...")
                continue
                
            print(f"\n[{i}/{len(restaurants)}] 📌 {restaurant['name']}의 리뷰 수집 중...")
            reviews = get_reviews_with_selenium(
                restaurant['name'], 
                restaurant['id'],
                restaurant['district']
            )
            
            if reviews:
                save_reviews_to_db(supabase, reviews)
                print(f"✅ {restaurant['name']} 리뷰 저장 완료 ({len(reviews)}개)")
            else:
                print(f"⚠️ {restaurant['name']} 리뷰 없음")
        except Exception as e:
            print(f"❌ {restaurant['name']} 처리 중 오류 발생: {str(e)}")
            continue
            
        time.sleep(2)

if __name__ == "__main__":
    load_dotenv()
    DB_URL = os.getenv("DB_URL")
    DB_KEY = os.getenv("DB_KEY")
    supabase: Client = create_client(DB_URL, DB_KEY)
    
    main(supabase)

