from fastapi import FastAPI
# from .router.youtube import get_channel_playlist
from app.test import testt

app = FastAPI()

@app.get('/')
def read_root():
    return {"msg: amu app server is running"}

@app.get('/test')
async def test():
    return await testt("강남구", 3)

# @app.get('/youtube/playlist')
# async def get_playlist_videos(channel_name: str, playlist_name: str):
#     return await get_channel_playlist(channel_name, playlist_name)