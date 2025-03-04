from dotenv import load_dotenv
load_dotenv()

import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("DB_URL")
SUPABASE_KEY = os.getenv("DB_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
