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