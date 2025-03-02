from fastapi import FastAPI, HTTPException
from googleapiclient.discovery import build
import os
from typing import Dict, Optional, List

app = FastAPI()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

async def get_channel_playlist(channel_name: str, playlist_name: str) -> Dict:
    channel = await find_channel(channel_name)
    
    playlist_id = await find_playlist(channel['id'], playlist_name)
    if not playlist_id:
        raise HTTPException(status_code=404, detail="해당 이름의 재생목록을 찾을 수 없습니다")
    
    videos = await get_playlist_videos(playlist_id)
    
    return {
        'channel': channel,
        'playlist': {
            'id': playlist_id,
            'title': playlist_name
        },
        'videos': videos
    }

async def find_channel(channel_name: str) -> Dict:
    search_request = youtube.search().list(
        part="snippet",
        q=channel_name,
        type="channel",
        maxResults=1
    )
    search_response = search_request.execute()
    
    if not search_response['items']:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다")
    
    return {
        'id': search_response['items'][0]['id']['channelId'],
        'title': search_response['items'][0]['snippet']['title']
    }

async def find_playlist(channel_id: str, playlist_name: str) -> Optional[str]:
    next_page_token = None
    
    while True:
        playlist_request = youtube.playlists().list(
            part="snippet",
            channelId=channel_id,
            maxResults=50,
            pageToken=next_page_token
        )
        playlist_response = playlist_request.execute()
        
        for item in playlist_response['items']:
            if playlist_name.lower() in item['snippet']['title'].lower():
                return item['id']
        
        next_page_token = playlist_response.get('nextPageToken')
        if not next_page_token:
            break
    
    return None

async def get_video_details(video_id: str) -> Dict:
    video_request = youtube.videos().list(
        part="statistics,snippet",
        id=video_id
    )
    video_response = video_request.execute()
    
    if not video_response['items']:
        return None
    
    video_info = video_response['items'][0]
    return {
        'like_count': video_info['statistics'].get('likeCount', '0'),
        'view_count': video_info['statistics'].get('viewCount', '0')
    }

async def get_playlist_videos(playlist_id: str) -> List[Dict]:
    videos = []
    next_page_token = None
    
    while True:
        playlist_items_request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        playlist_items_response = playlist_items_request.execute()
        
        for item in playlist_items_response['items']:
            video_id = item['contentDetails']['videoId']
            video_stats = await get_video_details(video_id)
            
            if video_stats:
                video_data = {
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'video_id': video_id,
                    'thumbnail': item['snippet']['thumbnails']['default']['url'],
                    'published_at': item['snippet']['publishedAt'],
                    **video_stats
                }
                videos.append(video_data)
        
        next_page_token = playlist_items_response.get('nextPageToken')
        if not next_page_token:
            break
    
    return videos

