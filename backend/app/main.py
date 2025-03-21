from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db.supabase import supabase
from backend.app.get_restaurants import get_restaurants
from backend.app.services.api.get_analysis import get_analysis_with_district

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def read_root():
    return {"msg": "amu app server is running"}

@app.get('/restaurants/{district}')
async def get_restaurants_api(district: str):
    
    return await get_restaurants(district) 

@app.get('/analysis/district/{district}')
# http://localhost:8000/analysis/district/강남구
async def get_analysis_api(district: str):
    
    analysis = get_analysis_with_district(supabase, district)
        
    return [analysis.model_dump() for analysis in analysis]