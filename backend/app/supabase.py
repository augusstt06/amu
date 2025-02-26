from typing import TypedDict, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

url = os.getenv('DB_URL')
key = os.getenv('DB_KEY')

supabase: Client = create_client(url, key)

def get_all_restaurants():
    try:
        query = supabase.table('restaurants').select('*')
        res = query.execute()
        return res.data
    except Exception as e:
        print("Error details:", str(e))
        print("Error type:", type(e))
        import traceback
        print("Full traceback:", traceback.format_exc())
        return []
    
class RestaurantData(TypedDict):
    restaurant_id: str
    name: str
    address: str
    category: str
    telephone: str
    latitude: float
    longitude: float
    rating: float

def save_restaurant_to_db(restaurant_data: RestaurantData) -> Optional[dict]:
    required_fields = ['restaurant_id', 'name', 'address', 'category', 'telephone', 'latitude', 'longitude', 'rating']
    missing_fields = [field for field in required_fields if restaurant_data.get(field) is None]

    if missing_fields:
        print(f"Missing required fields: {', '.join(missing_fields)}")
        return None
    
    try:
        existing = supabase.table('restaurants').select('*').eq('restaurant_id', restaurant_data['restaurant_id']).execute()
        
        if existing.data:
            # Update existing restaurant
            query = supabase.table('restaurants').update(restaurant_data).eq('restaurant_id', restaurant_data['restaurant_id']).execute()
        else:
            # Insert new restaurant
            query = supabase.table('restaurants').insert(restaurant_data).execute()
            
        return query.data[0]
    except Exception as e:
        print("Error details:", str(e))
        print("Error type:", type(e))
        import traceback
        print("Full traceback:", traceback.format_exc())
        return None