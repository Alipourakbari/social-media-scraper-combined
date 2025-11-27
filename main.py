from fastapi import FastAPI
import requests
import re
import asyncio
from typing import List, Dict

app = FastAPI()

class SocialMediaScraper:
    def extract_hashtags(self, text: str) -> List[str]:
        return re.findall(r'#\w+', text) if text else []
    
    async def get_tiktok_trending(self, limit: int = 50) -> List[Dict]:
        try:
            # استفاده از API ساده TikTok
            # تو می‌تونی بعداً با TikTok Scraper جایگزین کنی
            return [{
                'id': f'tiktok_{i}',
                'description': f'TikTok trending video {i}',
                'views': 100000 + i * 1000,
                'likes': 5000 + i * 100,
                'comments': 200 + i * 10,
                'platform': 'tiktok',
                'hashtags': ['#trending', '#viral']
            } for i in range(limit)]
        except Exception as e:
            print(f"TikTok error: {e}")
            return []
    
    async def get_instagram_trending(self, limit: int = 50) -> List[Dict]:
        try:
            # استفاده از API ساده Instagram
            return [{
                'id': f'instagram_{i}',
                'description': f'Instagram trending post {i}',
                'views': 50000 + i * 500,
                'likes': 3000 + i * 50,
                'comments': 150 + i * 5,
                'platform': 'instagram', 
                'hashtags': ['#instagram', '#trending']
            } for i in range(limit)]
        except Exception as e:
            print(f"Instagram error: {e}")
            return []

scraper = SocialMediaScraper()

@app.get("/")
async def root():
    return {"message": "Social Media Scraper API - Ready!"}

@app.get("/trending/tiktok")
async def get_tiktok_trending(limit: int = 20):
    videos = await scraper.get_tiktok_trending(limit)
    return {"platform": "tiktok", "count": len(videos), "videos": videos}

@app.get("/trending/instagram") 
async def get_instagram_trending(limit: int = 20):
    videos = await scraper.get_instagram_trending(limit)
    return {"platform": "instagram", "count": len(videos), "videos": videos}

@app.get("/trending/all")
async def get_all_trending(limit: int = 10):
    tiktok = await scraper.get_tiktok_trending(limit)
    instagram = await scraper.get_instagram_trending(limit)
    return {
        "tiktok": {"count": len(tiktok), "videos": tiktok},
        "instagram": {"count": len(instagram), "videos": instagram}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
