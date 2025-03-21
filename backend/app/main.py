from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db.supabase import supabase
from backend.app.get_restaurants import get_restaurants
from backend.app.services.api.get_analysis import get_analysis_with_district
from backend.app.services.api.get_recommand import get_recommendations, get_category_name


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

@app.get('/recommendations/{district}/{category}')
async def get_recommendations_api(district: str, category: str):
    try:
        category_name = get_category_name(category)
        if not category_name:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {category}. Valid categories are: hangover, solo, anniversary, simple"
            )
            
        recommendations = get_recommendations(supabase, district, category)
        return {
            "category_name": category_name,
            "recommendations": recommendations
        }
        
    except ValueError as e: 
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
