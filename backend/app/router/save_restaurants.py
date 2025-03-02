import os
import time
import requests
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv
from app.constant import SEOUL_DISTRICTS, FRANCHISES

load_dotenv()   


DB_URL = os.getenv("DB_URL")
DB_KEY = os.getenv("DB_KEY")

supabase: Client = create_client(DB_URL, DB_KEY)


NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NAVER_SEARCH_URL = os.getenv("NAVER_SEARCH_URL")

HEADERS = {
    "X-Naver-Client-Id": NAVER_CLIENT_ID,
    "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
}

def is_franchise(restaurant_name):
    for franchise in FRANCHISES:
        if franchise.lower() in restaurant_name.lower():
            return True
    return False

def fetch_restaurants(district):
    all_items = []
    display = 60 
    
    for start in range(1, display + 1, 5): 
        url = NAVER_SEARCH_URL
        params = {
            "query": f"서울 {district} 맛집",
            "display": "5",
            "start": str(start),
            "sort": "comment"
        }
        
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            print(f"❌ {district} 데이터 요청 실패: {response.status_code}")
            break
        
        data = response.json()
        items = data.get("items", [])
        all_items.extend(items)
        
        
        if len(items) < 5:
            break
            
        time.sleep(0.1)
    
    return all_items

def save_to_db(restaurants, district):
    for item in restaurants:
        restaurant_name = item["title"].replace("<b>", "").replace("</b>", "")
        
        if is_franchise(restaurant_name):
            print(f"⚠️ 프랜차이즈 제외: {restaurant_name}")
            continue
        
        restaurant_id = str(uuid.uuid4())

        restaurant_data = {
            "id": restaurant_id,
            "name": item["title"].replace("<b>", "").replace("</b>", ""),
            "category": item.get("category", ""),
            "description": item.get("description", ""),
            "phone": item.get("telephone", ""),
            "address": item.get("roadAddress", ""),
            "district": district, 
            "map_x": float(item["mapx"]),
            "map_y": float(item["mapy"]),
        }

        supabase.table("restaurants").insert(restaurant_data).execute()

def main():
    
    for district in SEOUL_DISTRICTS:
        print(f"📌 {district}의 식당 데이터 수집 중...")
        restaurants = fetch_restaurants(district)
        
        if restaurants:
            save_to_db(restaurants, district)
            print(f"✅ {district} 저장 완료 ({len(restaurants)}개)")
        else:
            print(f"⚠️ {district} 데이터 없음")
        
        time.sleep(1)  # API 요청 속도 제한

if __name__ == "__main__":
    main()
