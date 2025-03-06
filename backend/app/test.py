from fastapi import APIRouter, HTTPException
import requests
import os
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

router = APIRouter()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NAVER_SEARCH_URL = os.getenv("NAVER_SEARCH_URL")

HEADERS = {
    "X-Naver-Client-Id": NAVER_CLIENT_ID,
    "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
}

async def testt(district: str, start: int = 1):

    try:
        all_items = []
        
        for i in range(2):
            current_start = start + (i * 5)
            query = f"서울 {district} 맛집"
            encoded_query = urllib.parse.quote(query)
            
            url = f"{NAVER_SEARCH_URL}?query={encoded_query}&display=5&start={current_start}&sort=comment"
            
            print(f"\n=== API 요청 URL ===")
            print(url)
            
            response = requests.get(url, headers=HEADERS)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="API 요청 실패")
            
            data = response.json()
            items = data.get("items", [])
            all_items.extend(items)
        
        return {"items": all_items}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))