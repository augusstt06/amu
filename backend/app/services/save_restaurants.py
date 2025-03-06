from dotenv import load_dotenv
load_dotenv()   
import os
import time
import requests
import uuid
from app.db.supabase import create_client, Client
from app.constant import SEOUL_DISTRICTS, FRANCHISES
from app.models.restaurant import Restaurant



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
    total_items = 60 
    
    for start in range(1, total_items + 1, 5): 
        url = NAVER_SEARCH_URL
        params = {
            "query": f"서울 {district} 맛집",
            "display": 5,
            "start": start,
            "sort": "comment"
        }
        
        
        full_url = f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        print(f"\n=== {district} API 요청 URL ===")
        print(full_url)
        
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            print(f"❌ {district} 데이터 요청 실패: {response.status_code}")
            break
        
        data = response.json()
        
        items = data.get("items", [])

        if not items:  
            print(f"⚠️ 더 이상 데이터가 없습니다.")
            break
            
        all_items.extend(items)
        
        if len(all_items) >= total_items:  
            # print(f"✅ 목표 개수({total_items}개) 도달")
            break
            
        time.sleep(0.1)
    
    # print(f"\n=== {district} 총 수집 결과 ===")
    # print(f"총 {len(all_items)}개의 식당 데이터 수집 완료")
    return all_items

def save_to_db(restaurants, district):
    for item in restaurants:
        restaurant_name = item["title"].replace("<b>", "").replace("</b>", "")
        address = item.get("roadAddress", "")
        
        if is_franchise(restaurant_name):
            print(f"⚠️ 프랜차이즈 제외: {restaurant_name}")
            continue
        

        existing_restaurant = supabase.table("restaurants").select("id").eq("name", restaurant_name).eq("address", address).execute()
        
        if existing_restaurant.data:
            print(f"⚠️ 중복 식당 스킵: {restaurant_name}")
            continue
        
        restaurant_id = str(uuid.uuid4())

        restaurant = Restaurant(
                id=restaurant_id,
                name=restaurant_name,
                category=item.get("category", ""),
                description=item.get("description", ""),
                phone=item.get("telephone", ""),
                address=address,
                map_x=float(item["mapx"]),
                map_y=float(item["mapy"])
            )

        restaurant_data = restaurant.model_dump()
        supabase.table("restaurants").insert(restaurant_data).execute()
        print(f"✅ 식당 저장 완료: {restaurant_name}")

def main():
    
    for district in SEOUL_DISTRICTS:
        print(f"📌 {district}의 식당 데이터 수집 중...")
        restaurants = fetch_restaurants(district)
        
        if restaurants:
            save_to_db(restaurants, district)
            print(f"✅ {district} 저장 완료 ({len(restaurants)}개)")
        else:
            print(f"⚠️ {district} 데이터 없음")
        
        time.sleep(1)  

if __name__ == "__main__":
    main()
