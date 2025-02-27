from fastapi import FastAPI
from .maps import search_restaurant
from .youtube import get_channel_playlist

app = FastAPI()

@app.get('/')
def read_root():
    return {"msg: amu app server is running"}

@app.get('/restaurants')
def get_restaurants(query: str):
    return search_restaurant(query)


@app.get('/youtube/playlist')
async def get_playlist_videos(channel_name: str, playlist_name: str):
    return await get_channel_playlist(channel_name, playlist_name)