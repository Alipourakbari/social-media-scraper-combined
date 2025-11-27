from fastapi import FastAPI
import requests
import re
import asyncio
import os
import json
from datetime import datetime
from typing import List, Dict
import aiohttp

app = FastAPI()

# گرفتن توکن‌ها از Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8361557378:AAEntX7ri-he2foBASD4JPGvfSzBLMS3Spg")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5800900434")

class VideoDownloader:
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def download_tiktok_no_watermark(self, video_url: str) -> str:
        """دانلود ویدیو TikTok بدون واترمارک"""
        try:
            session = await self.get_session()
            
            # استفاده از سرویس‌های دانلود TikTok بدون واترمارک
            apis = [
                f"https://www.tikwm.com/api/?url={video_url}",
                f"https://tikdown.org/api?url={video_url}",
                f"https://twitsave.com/info?url={video_url}"
            ]
            
            for api_url in apis:
                try:
                    async with session.get(api_url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('data', {}).get('play'):
                                return data['data']['play']
                            elif data.get('url'):
                                return data['url']
                except:
                    continue
            
            return None
        except Exception as e:
            print(f"TikTok download error: {e}")
            return None
    
    async def download_instagram_no_watermark(self, post_url: str) -> str:
        """دانلود ویدیو/post اینستاگرام بدون واترمارک"""
        try:
            session = await self.get_session()
            
            apis = [
                f"https://instasupersave.com/api/ig?url={post_url}",
                f"https://igram.io/api/ig?url={post_url}",
                f"https://saveig.app/api/ajaxSearch?url={post_url}"
            ]
            
            for api_url in apis:
                try:
                    async with session.get(api_url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            # استخراج لینک ویدیو از پاسخ API
                            if data.get('links'):
                                for link in data['links']:
                                    if link.get('quality') == 'hd':
                                        return link['url']
                            elif data.get('url'):
                                return data['url']
                except:
                    continue
            
            return None
        except Exception as e:
            print(f"Instagram download error: {e}")
            return None
    
    async def download_youtube_shorts(self, video_url: str) -> str:
        """دانلود YouTube Shorts"""
        try:
            session = await self.get_session()
            
            # استفاده از yt-dlp through public APIs
            apis = [
                f"https://co.wuk.sh/api/json?url={video_url}",
                f"https://yt5s.com/en/api/convert?url={video_url}"
            ]
            
            for api_url in apis:
                try:
                    async with session.get(api_url, timeout=15) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('url'):
                                return data['url']
                            elif data.get('downloadUrl'):
                                return data['downloadUrl']
                except:
                    continue
            
            return None
        except Exception as e:
            print(f"YouTube download error: {e}")
            return None

class SocialMediaScraper:
    def __init__(self):
        self.telegram_token = TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = TELEGRAM_CHAT_ID
        self.downloader = VideoDownloader()
    
    def send_to_telegram(self, message: str):
        """ارسال پیام به تلگرام"""
        if not self.telegram_token or not self.telegram_chat_id:
            print("❌ Telegram token or chat ID not set")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, data=data)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram send error: {e}")
            return False
    
    async def send_video_to_telegram(self, video_url: str, caption: str):
        """ارسال ویدیو به تلگرام"""
        if not video_url:
            return False
            
        try:
            # دانلود ویدیو
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as response:
                    if response.status == 200:
                        video_data = await response.read()
                        
                        # آپلود به تلگرام
                        url = f"https://api.telegram.org/bot{self.telegram_token}/sendVideo"
                        data = {
                            "chat_id": self.telegram_chat_id,
                            "caption": caption,
                            "parse_mode": "HTML"
                        }
                        files = {
                            "video": ("video.mp4", video_data, "video/mp4")
                        }
                        
                        response = requests.post(url, data=data, files=files)
                        return response.status_code == 200
        except Exception as e:
            print(f"Telegram video send error: {e}")
            return False
    
    def extract_hashtags(self, text: str) -> List[str]:
        return re.findall(r'#\w+', text) if text else []
    
    async def get_tiktok_trending(self, limit: int = 20) -> List[Dict]:
        """دریافت ترندهای TikTok با لینک دانلود"""
        try:
            videos = []
            for i in range(limit):
                # شبیه‌سازی ویدیوهای ترند (در نسخه واقعی از API استفاده می‌شه)
                video_data = {
                    'id': f'tiktok_{i}',
                    'description': f'ویدیوی ترند تیک‌تاک شماره {i+1} - این ویدیو در حال حاضر ترند شده است! 🎵',
                    'views': 500000 + i * 25000,
                    'likes': 25000 + i * 1200,
                    'comments': 1500 + i * 80,
                    'platform': 'tiktok',
                    'hashtags': ['#ترند', '#تیک‌تاک', '#ویدیو', '#ایران'],
                    'url': f'https://www.tiktok.com/@creator/video/7{i}123456789',
                    'download_url': None
                }
                
                # دریافت لینک دانلود بدون واترمارک
                download_url = await self.downloader.download_tiktok_no_watermark(video_data['url'])
                video_data['download_url'] = download_url
                
                videos.append(video_data)
                
                # ارسال ویدیو به تلگرام اگر دانلود موفق بود
                if download_url:
                    caption = f"""
🎵 <b>تیک‌تاک ترند</b>
────────────────────
📝 {video_data['description']}
👁️ {video_data['views']:,} بازدید
❤️ {video_data['likes']:,} لایک
💬 {video_data['comments']:,} کامنت
🔗 <a href="{video_data['url']}">لینک اصلی</a>
"""
                    await self.send_video_to_telegram(download_url, caption)
            
            # ارسال گزارش
            report = f"""
📊 <b>گزارش TikTok - {datetime.now().strftime('%Y/%m/%d')}</b>
────────────────────
🎯 تعداد ویدیوها: <b>{len(videos)}</b>
✅ با موفقیت دانلود شد: <b>{len([v for v in videos if v['download_url']])}</b>
"""
            self.send_to_telegram(report)
            
            return videos
        except Exception as e:
            error_msg = f"❌ خطا در دریافت ترندهای تیک‌تاک: {str(e)}"
            self.send_to_telegram(error_msg)
            return []
    
    async def get_instagram_trending(self, limit: int = 20) -> List[Dict]:
        """دریافت ترندهای Instagram با لینک دانلود"""
        try:
            videos = []
            for i in range(limit):
                video_data = {
                    'id': f'instagram_{i}',
                    'description': f'پست ترند اینستاگرام شماره {i+1} - این پست در اکسپلور در حال دیده شدن است! 📸',
                    'views': 300000 + i * 15000,
                    'likes': 18000 + i * 900,
                    'comments': 800 + i * 40,
                    'platform': 'instagram', 
                    'hashtags': ['#اینستاگرام', '#ترند', '#اکسپلور', '#پست'],
                    'url': f'https://www.instagram.com/p/ABC{i}123456/',
                    'download_url': None
                }
                
                # دریافت لینک دانلود بدون واترمارک
                download_url = await self.downloader.download_instagram_no_watermark(video_data['url'])
                video_data['download_url'] = download_url
                
                videos.append(video_data)
                
                # ارسال ویدیو به تلگرام
                if download_url:
                    caption = f"""
📸 <b>اینستاگرام ترند</b>
────────────────────
📝 {video_data['description']}
👁️ {video_data['views']:,} بازدید  
❤️ {video_data['likes']:,} لایک
💬 {video_data['comments']:,} کامنت
🔗 <a href="{video_data['url']}">لینک اصلی</a>
"""
                    await self.send_video_to_telegram(download_url, caption)
            
            # ارسال گزارش
            report = f"""
📊 <b>گزارش Instagram - {datetime.now().strftime('%Y/%m/%d')}</b>
────────────────────
🎯 تعداد پست‌ها: <b>{len(videos)}</b>
✅ با موفقیت دانلود شد: <b>{len([v for v in videos if v['download_url']])}</b>
"""
            self.send_to_telegram(report)
            
            return videos
        except Exception as e:
            error_msg = f"❌ خطا در دریافت ترندهای اینستاگرام: {str(e)}"
            self.send_to_telegram(error_msg)
            return []

scraper = SocialMediaScraper()

@app.get("/")
async def root():
    return {"message": "🤖 ربات دانلود ویدیوهای ترند بدون واترمارک فعال است!"}

@app.get("/download/tiktok")
async def download_tiktok_trending(limit: int = 10):
    """دانلود ترندهای TikTok"""
    videos = await scraper.get_tiktok_trending(limit)
    return {
        "platform": "tiktok", 
        "count": len(videos),
        "downloaded": len([v for v in videos if v['download_url']]),
        "videos": videos
    }

@app.get("/download/instagram") 
async def download_instagram_trending(limit: int = 10):
    """دانلود ترندهای Instagram"""
    videos = await scraper.get_instagram_trending(limit)
    return {
        "platform": "instagram", 
        "count": len(videos),
        "downloaded": len([v for v in videos if v['download_url']]),
        "videos": videos
    }

@app.get("/download/all")
async def download_all_trending(limit: int = 5):
    """دانلود تمام ترندها"""
    tiktok = await scraper.get_tiktok_trending(limit)
    instagram = await scraper.get_instagram_trending(limit)
    
    total_downloaded = (len([v for v in tiktok if v['download_url']]) + 
                       len([v for v in instagram if v['download_url']]))
    
    summary = f"""
🎉 <b>دانلود کامل انجام شد</b>
────────────────────
📅 تاریخ: {datetime.now().strftime('%Y/%m/%d %H:%M')}
📊 تعداد کل: <b>{len(tiktok) + len(instagram)}</b>
✅ دانلود موفق: <b>{total_downloaded}</b>
🎵 تیک‌تاک: <b>{len(tiktok)}</b>
📸 اینستاگرام: <b>{len(instagram)}</b>
"""
    scraper.send_to_telegram(summary)
    
    return {
        "tiktok": {"count": len(tiktok), "downloaded": len([v for v in tiktok if v['download_url']]), "videos": tiktok},
        "instagram": {"count": len(instagram), "downloaded": len([v for v in instagram if v['download_url']]), "videos": instagram},
        "total_downloaded": total_downloaded
    }

@app.get("/test-download")
async def test_download():
    """تست دانلود"""
    # تست با یک لینک نمونه
    test_url = "https://www.tiktok.com/@example/video/123456789"
    download_url = await scraper.downloader.download_tiktok_no_watermark(test_url)
    
    return {
        "test_url": test_url,
        "download_url": download_url,
        "status": "success" if download_url else "failed"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
