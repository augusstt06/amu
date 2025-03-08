from fastapi import FastAPI

from backend.app.get_restaurants import get_restaurants

app = FastAPI()

@app.get('/')
def read_root():
    return {"msg": "amu app server is running"}

@app.get('/restaurants/{district}')
async def get_restaurants_api(district: str):
    
    return await get_restaurants(district) 

