from fastapi import FastAPI
from .supabase import get_all_restaurants
from .maps import search_restaurant
app = FastAPI()

@app.get('/')
def read_root():
    return {"msg: amu app server is running"}

@app.get('/restaurants')
def get_restaurants(query: str):
    return search_restaurant(query)
    # return get_all_restaurants()


