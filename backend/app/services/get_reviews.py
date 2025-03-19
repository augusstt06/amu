# FIXME: db에 존재하는 식당 스킵.

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
from app.services.analyze_reviews import analyze_reviews
from app.models.analyze import Analyze
import numpy as np

def generate_review_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

def initialize_driver() -> webdriver.Chrome:
    chrome_options = Options()
    # chrome_options.add_argument('--headless') => 수정 필요
    chrome_options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=chrome_options)

def search_restaurant(driver: webdriver.Chrome, restaurant_name: str, district: str) -> bool:
    try:
        search_url = f"https://map.naver.com/p/search/{restaurant_name}"
        driver.get(search_url)
        time.sleep(3)
        
        search_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#searchIframe"))
        )
        driver.switch_to.frame(search_iframe)
        print("✅ searchIframe 진입 완료")
        return True
    except Exception as e:
        print(f"❌ 검색 실패: {str(e)}")
        return False

def navigate_to_reviews_direct(driver: webdriver.Chrome) -> bool:
    try:
        current_url = driver.current_url
        review_url = current_url.split("?")[0] + "?c=15.00,0,0,0,dh&placePath=/review&isCorrectAnswer=true"
        driver.get(review_url)
        time.sleep(3)
        
        driver.switch_to.default_content()
        entry_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#entryIframe"))
        )
        driver.switch_to.frame(entry_iframe)
        time.sleep(2)
        print("✅ 리뷰 페이지 직접 이동 성공")
        return True
    except TimeoutException:
        print("⚠️ 직접 이동 실패")
        return False

def find_restaurant_by_district(driver: webdriver.Chrome, restaurant_name: str, district: str) -> bool:
    try:
        driver.get(f"https://map.naver.com/p/search/{restaurant_name}")
        time.sleep(3)
        
        driver.switch_to.default_content()
        search_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#searchIframe"))
        )
        driver.switch_to.frame(search_iframe)
        
        results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.VLTHu"))
        )
        
        for result in results[:5]:
            try:
                address = result.find_element(By.CSS_SELECTOR, "span.Pb4bU").text
                title = result.find_element(By.CSS_SELECTOR, "span.YwYLL").text
                print(f"검색 결과: {title} / 주소: {address}")
                
                if any(part in address for part in district.split()):
                    print(f"✅ District 매칭 성공: {title} ({address})")
                    result.find_element(By.CSS_SELECTOR, "span.YwYLL").click()
                    time.sleep(3)
                    return True
            except NoSuchElementException:
                continue
        
        print("⚠️ 매칭되는 매장을 찾을 수 없습니다.")
        return False
    except Exception as e:
        print(f"❌ 매장 검색 실패: {str(e)}")
        return False

def navigate_to_review_tab(driver: webdriver.Chrome) -> bool:
    try:
        driver.switch_to.default_content()
        entry_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#entryIframe"))
        )
        driver.switch_to.frame(entry_iframe)
        
        review_tab = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='review']"))
        )
        review_tab.click()
        time.sleep(3)
        print("✅ 리뷰 탭 진입 성공")
        return True
    except Exception as e:
        print(f"❌ 리뷰 탭 진입 실패: {str(e)}")
        return False

def extract_reviews(driver: webdriver.Chrome, restaurant_id: str) -> list[dict]:
    try:
        driver.switch_to.default_content()
        entry_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#entryIframe"))
        )
        driver.switch_to.frame(entry_iframe)
        time.sleep(2)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.place_section"))
        )
        
        try:
            more_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.fvwqf"))
            )
            more_button.click()
            time.sleep(2)
        except:
            pass
        
        review_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.place_apply_pui"))
        )
        
        reviews = []
        review_texts = []
        ratings = []
        
        # 최대 20개까지 수집하면서 진행상황 출력
        for i, review_element in enumerate(review_elements[:20], 1):
            try:
                review_text = review_element.find_element(By.CSS_SELECTOR, "div.pui__vn15t2 a").text
                review_texts.append(review_text)
                
                try:
                    rating_element = review_element.find_element(By.CSS_SELECTOR, "span.pui__jhpEyP")
                    rating = 5.0 if rating_element.text else None
                    ratings.append(rating)
                except NoSuchElementException:
                    ratings.append(None)
                
                review = {
                    'restaurant_id': restaurant_id,
                    'review_text': review_text,
                    'rating': rating,
                    'review_hash': generate_review_hash(review_text)
                }
                reviews.append(review)
            except Exception as e:
                continue
        
        print()  
        return reviews
    except Exception as e:
        print(f"\n❌ 리뷰 추출 실패: {str(e)}")
        return []

def get_reviews_with_selenium(restaurant_name: str, restaurant_id: str, district: str) -> list[dict]:
    driver = None
    try:
        driver = initialize_driver()
        print(f"🌐 '{restaurant_name}' 검색 중... (지역: {district})")
        
        if not search_restaurant(driver, restaurant_name, district):
            return []
            
        if navigate_to_reviews_direct(driver):
            return extract_reviews(driver, restaurant_id)
            
        print("⚠️ 직접 이동 실패, district 매칭 시도...")
        if find_restaurant_by_district(driver, restaurant_name, district):
            if navigate_to_review_tab(driver):
                return extract_reviews(driver, restaurant_id)
                
        return []
        
    except Exception as e:
        print(f"❌ 전체 프로세스 실패: {str(e)}")
        return []
    finally:
        if driver:
            driver.quit()

def calculate_rating_reliability(sentiment_score: float, user_ratings: list[float]) -> float:
    if not user_ratings:
        return 0.0
        
    normalized_sentiment = sentiment_score / 2
    
    avg_rating = np.mean(user_ratings)
    difference = abs(normalized_sentiment - avg_rating)
    

    reliability = (1 - (difference / 5)) * 100
    
    return max(0, min(100, reliability))  

def main(supabase: Client):
    response = supabase.table("restaurants").select("id, name, district").execute()
    restaurants = response.data
    
    print(f"총 {len(restaurants)}개의 레스토랑을 찾았습니다.")
    
    for i, restaurant in enumerate(restaurants, 1):
        try:
            print(f"\n[{i}/{len(restaurants)}] 📌 {restaurant['name']}의 리뷰 수집 중...")
            reviews = get_reviews_with_selenium(
                restaurant['name'], 
                restaurant['id'],
                restaurant['district']
            )
            
            if reviews:
                review_texts = [review['review_text'] for review in reviews]
                ratings = [review['rating'] for review in reviews if review['rating'] is not None]
                
                print(f"\n리뷰 분석 중... (총 {len(review_texts)}개)")
                analysis_result = analyze_reviews(review_texts, ratings)
                if analysis_result:
                    sentiment_score = analysis_result['sentiment_score']
                    rating_reliability = calculate_rating_reliability(sentiment_score, ratings)
                    
                    print("\n📊 분석 결과:")
                    print(f"감성 점수: {sentiment_score:.2f}/10")
                    print(f"리뷰 요약: {analysis_result['review_summary']}")
                    print(f"분석한 리뷰 수: {analysis_result['review_count']}")
                    print(f"평균 평점: ⭐ {analysis_result['average_rating']:.1f}/5.0")
                    print(f"평점 신뢰도: {rating_reliability:.1f}%")
                    
                    analyze = Analyze(
                        restaurant_id=restaurant['id'],
                        name=restaurant['name'],
                        sentiment_score=sentiment_score,
                        review_summary=analysis_result['review_summary'],
                        rating_reliability=rating_reliability,
                        average_rating=analysis_result['average_rating']
                    )
                    
                    try:
                        analyze_data = analyze.model_dump(exclude={'id', 'created_at'})
                        analyze_data['restaurant_id'] = str(analyze_data['restaurant_id'])  # UUID를 문자열로 변환
                        
                        # 기존 분석 결과가 있는지 확인
                        existing = supabase.table("analyze").select("id").eq("restaurant_id", analyze_data['restaurant_id']).execute()
                        
                        if existing.data:
                            # 기존 데이터가 있으면 업데이트
                            supabase.table("analyze").update(analyze_data).eq("restaurant_id", analyze_data['restaurant_id']).execute()
                            print("✅ 분석 결과 업데이트 완료")
                        else:
                            # 새로운 데이터 삽입
                            supabase.table("analyze").insert(analyze_data).execute()
                            print("✅ 분석 결과 저장 완료")
                    except Exception as e:
                        print(f"❌ 분석 결과 저장 실패: {str(e)}")
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

