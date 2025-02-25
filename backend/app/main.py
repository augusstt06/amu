from fastapi import FastAPI
from .supabase import get_all_restaurants

app = FastAPI()

@app.get('/')
def read_root():
    return {"msg: amu app server is running"}

@app.get('/restaurants')
def get_restaurants():
    return get_all_restaurants()


