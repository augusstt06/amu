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

KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")
KAKAO_SEARCH_URL = os.getenv("KAKAO_SEARCH_URL")

HEADERS = {
    "Authorization": f"KakaoAK {KAKAO_API_KEY}"
}

def is_franchise(restaurant_name):
    for franchise in FRANCHISES:
        if franchise.lower() in restaurant_name.lower():
            return True
    return False

def fetch_restaurants(district):
    all_items = []
    page = 1
    size = 15  
    
    while True:
        url = KAKAO_SEARCH_URL
        params = {
            "query": f"서울 {district} 맛집",
            "page": page,
            "size": size
        }
        
        
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            print(f"❌ {district} 데이터 요청 실패: {response.status_code}")
            print(f"응답 내용: {response.text}")
            break
        
        data = response.json()
        items = data.get("documents", [])
        
        if not items:
            print(f"⚠️ 더 이상 데이터가 없습니다.")
            break
            
        all_items.extend(items)
        
        if data.get("meta", {}).get("is_end", True):
            break
            
        page += 1
        time.sleep(0.1) 
    
    print(f"\n=== {district} 총 수집 결과 ===")
    print(f"총 {len(all_items)}개의 식당 데이터 수집 완료")
    return all_items

def save_to_db(restaurants, district):
    saved_count = 0
    skipped_count = 0
    
    for item in restaurants:
        restaurant_name = item["place_name"]
        address = item.get("road_address_name", "")
        
        if is_franchise(restaurant_name):
            print(f"⚠️ 프랜차이즈 제외: {restaurant_name}")
            skipped_count += 1
            continue
        
        existing_restaurant = supabase.table("restaurants").select("id").eq("name", restaurant_name).eq("road_address", address).execute()
        
        if existing_restaurant.data:
            print(f"⚠️ 중복 식당 스킵: {restaurant_name}")
            skipped_count += 1
            continue
        
        restaurant_id = str(uuid.uuid4())

        try:
            restaurant = Restaurant(
                id=restaurant_id,
                name=restaurant_name,
                category=item.get("category_name", ""),
                address=item.get("address_name", ""),
                road_address=item.get("road_address_name", ""),
                phone=item.get("phone", ""),
                place_url=item.get("place_url", ""),
                map_x=float(item["x"]),
                map_y=float(item["y"]),
                district=district
            )

            restaurant_data = restaurant.model_dump()
            supabase.table("restaurants").insert(restaurant_data).execute()
            print(f"✅ 식당 저장 완료: {restaurant_name}")
            saved_count += 1
            
        except Exception as e:
            print(f"❌ 식당 저장 실패: {restaurant_name}")
            print(f"에러 내용: {str(e)}")
            continue

    print(f"\n=== {district} 저장 결과 ===")
    print(f"저장 완료: {saved_count}개")
    print(f"건너뛴 항목: {skipped_count}개")

def main():
    total_saved = 0
    total_districts = len(SEOUL_DISTRICTS)
    
    print("🚀 서울시 맛집 데이터 수집 시작")
    
    for idx, district in enumerate(SEOUL_DISTRICTS, 1):
        print(f"\n[{idx}/{total_districts}] 📌 {district}의 식당 데이터 수집 중...")
        restaurants = fetch_restaurants(district)
        
        if restaurants:
            save_to_db(restaurants, district)
            total_saved += len(restaurants)
        else:
            print(f"⚠️ {district} 데이터 없음")
        
        time.sleep(1)  
    
    print("\n🎉 데이터 수집 완료")
    print(f"총 {total_saved}개의 식당 데이터 처리")

if __name__ == "__main__":
    main()
