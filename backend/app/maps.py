from typing import TypedDict, List
from dotenv import load_dotenv
import os
import requests

load_dotenv()

class RestaurantData(TypedDict):
    restaurant_id: str
    name: str
    address: str
    category: str
    telephone: str
    latitude: float
    longitude: float
    rating: float

def search_restaurant(query: str) -> List[RestaurantData]:
    NAVER_SEARCH_URL = os.getenv('NAVER_SEARCH_URL')
    NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
    NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')
    
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print('There is no Naver API authentication information.')
        return []
    headers = {
        'X-Naver-Client-Id': NAVER_CLIENT_ID,
        'X-Naver-Client-Secret': NAVER_CLIENT_SECRET,
    }
    url = NAVER_SEARCH_URL
    params = {
        'query': f"{query} 맛집",
        'display': 10,
    }
    
    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        results = res.json().get('items', [])

        restaurants: List[RestaurantData] = []
        for item in results:
            name = item.get('title', '').replace('<b>', '').replace('</b>', '')
            place_id = item.get('link', '').split('/')[-1]
            
            mapx = float(item.get('mapx', 0)) / 10000000
            mapy = float(item.get('mapy', 0)) / 10000000
            
            restaurant: RestaurantData = {
                'restaurant_id': place_id,
                'name': name,
                'address': item.get('address', ''),
                'category': item.get('category', '음식점'),
                'telephone': item.get('telephone', ''),
                'latitude': mapy,
                'longitude': mapx,
                'rating': 0.0  
            }
            
            if restaurant['name']:  
                restaurants.append(restaurant)
            
        return restaurants
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while requesting the API: {str(e)}")
        return []
    