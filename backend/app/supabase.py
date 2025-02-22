from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

url = os.getenv('DB_URL')
key = os.getenv('DB_KEY')

supabase: Client = create_client(url, key)