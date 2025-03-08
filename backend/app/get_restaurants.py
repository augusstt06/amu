from fastapi import APIRouter, HTTPException
import requests
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

KAKAO_API_KEY = os.getenv("KAKAO_API_KEY") 
KAKAO_SEARCH_URL = os.getenv("KAKAO_SEARCH_URL")

HEADERS = {
    "Authorization": f"KakaoAK {KAKAO_API_KEY}"
}

async def get_restaurants(district: str):
    try:
        all_items = []
        total_pages = 4  
        
        for page in range(1, total_pages + 1):
            query = f"서울 {district} 맛집"
            params = {
                "query": query,
                "page": page,
                "size": 15
            }
            
            print(f"\n=== {page}페이지 API 요청 ===")
            print(f"URL: {KAKAO_SEARCH_URL}")
            print(f"Params: {params}")
            
            response = requests.get(KAKAO_SEARCH_URL, headers=HEADERS, params=params)
            
            print(f"응답 상태 코드: {response.status_code}")
            
            if response.status_code != 200:
                print(f"에러 응답: {response.text}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"API 요청 실패: {response.text}"
                )
            
            data = response.json()
            items = data.get("documents", [])
            
            if not items:
                print("더 이상 결과가 없습니다.")
                break
                
            all_items.extend(items)
            
            if data.get("meta", {}).get("is_end", True):
                break
        
        print(f"\n총 {len(all_items)}개의 맛집 데이터 수집 완료")
        
        return {
            "items": all_items,
            "meta": {
                "total_count": len(all_items),
                "total_pages": page
            }
        }
        
    except Exception as e:
        print(f"=== 에러 발생 ===")
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))