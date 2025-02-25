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
    phone: str

    
def insert_restaurant(restaurant_data: RestaurantData) -> Optional[dict]:
    required_fields = ['restaurant_id', 'name', 'address', 'category', 'phone']
    missing_fields = [field for field in required_fields if not restaurant_data.get(field)]

    if missing_fields:
        print(f"Missing required fields: {', '.join(missing_fields)}")
        return None
    
    data = {field: restaurant_data.get(field) for field in required_fields}
    
    try:
        query = supabase.table('restaurants').insert(data).execute()
        return query.data[0]
    except Exception as e:
        print("Error details:", str(e))
        print("Error type:", type(e))
        import traceback
        print("Full traceback:", traceback.format_exc())
        return None