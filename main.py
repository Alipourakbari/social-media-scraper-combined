from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import requests
import re
import asyncio
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
import aiohttp
import urllib.parse

# ایجاد lifespan manager اول
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup events
    print("🚀 Starting Social Media Scraper...")
    
    # ایجاد نمونه‌ها
    app.state.scraper = SocialMediaScraper()
    
    # ارسال پیام راه‌اندازی
    app.state.scraper.telegram.send_message("""
🚀 <b>ربات راه‌اندازی شد</b>
────────────────────
🤖 Social Media Scraper v2.0
📅 {datetime.now().strftime('%Y/%m/%d %H:%M')}
📍 سرور: Railway
✅ وضعیت: <b>فعال</b>
────────────────────
آماده دریافت ترندها و دانلود ویدیو!
""")
    
    yield  # اینجا برنامه اجرا می‌شود
    
    # Shutdown events
    print("🔴 Shutting down Social Media Scraper...")
    await app.state.scraper.downloader.close_session()
    app.state.scraper.telegram.send_message("🔴 ربات متوقف شد")

# ایجاد FastAPI با lifespan
app = FastAPI(title="Social Media Scraper", version="2.0", lifespan=lifespan)

# Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8361557378:AAEntX7ri-he2foBASD4JPGvfSzBLMS3Spg")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5800900434")

class VideoDownloader:
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close_session(self):
        if self.session:
            await self.session.close()
    
    async def download_tiktok_no_watermark(self, video_url: str) -> Optional[str]:
        """دانلود ویدیو TikTok بدون واترمارک"""
        try:
            session = await self.get_session()
            apis = [
                f"https://www.tikwm.com/api/?url={video_url}",
                f"https://tikdown.org/api?url={video_url}",
            ]
            
            for api_url in apis:
                try:
                    async with session.get(api_url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            download_url = data.get('data', {}).get('play') or data.get('data', {}).get('wmplay') or data.get('url')
                            if download_url:
                                if not download_url.startswith('http'):
                                    download_url = 'https:' + download_url
                                return download_url
                except Exception as e:
                    print(f"API {api_url} failed: {e}")
                    continue
            return None
        except Exception as e:
            print(f"TikTok download error: {e}")
            return None
    
    async def download_instagram_no_watermark(self, post_url: str) -> Optional[str]:
        """دانلود ویدیو اینستاگرام بدون واترمارک"""
        try:
            session = await self.get_session()
            apis = [
                f"https://instasupersave.com/api/ig?url={post_url}",
                f"https://igram.io/api/ig?url={post_url}",
            ]
            
            for api_url in apis:
                try:
                    async with session.get(api_url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if isinstance(data, dict):
                                if data.get('links'):
                                    for link in data['links']:
                                        if link.get('quality') in ['hd', 'sd']:
                                            return link['url']
                                elif data.get('url'):
                                    return data['url']
                except Exception as e:
                    print(f"API {api_url} failed: {e}")
                    continue
            return None
        except Exception as e:
            print(f"Instagram download error: {e}")
            return None
    
    async def download_youtube_shorts(self, video_url: str) -> Optional[str]:
        """دانلود YouTube Shorts"""
        try:
            session = await self.get_session()
            apis = [
                f"https://co.wuk.sh/api/json?url={video_url}",
            ]
            
            for api_url in apis:
                try:
                    headers = {'Accept': 'application/json'}
                    async with session.get(api_url, headers=headers, timeout=15) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data.get('url')
                except Exception as e:
                    print(f"API {api_url} failed: {e}")
                    continue
            return None
        except Exception as e:
            print(f"YouTube download error: {e}")
            return None
    
    async def download_from_url(self, url: str) -> Optional[str]:
        """دانلود از هر URL با تشخیص خودکار پلتفرم"""
        if 'tiktok.com' in url:
            return await self.download_tiktok_no_watermark(url)
        elif 'instagram.com' in url:
            return await self.download_instagram_no_watermark(url)
        elif 'youtube.com/shorts' in url or 'youtu.be' in url:
            return await self.download_youtube_shorts(url)
        else:
            return None

class TelegramBotHandler:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """ارسال پیام به تلگرام"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram send error: {e}")
            return False
    
    async def send_video(self, video_url: str, caption: str = "") -> bool:
        """ارسال ویدیو به تلگرام"""
        if not video_url:
            return False
        
        try:
            # استفاده از sendDocument برای فایل‌های بزرگ
            url = f"{self.base_url}/sendDocument"
            data = {
                "chat_id": self.chat_id,
                "caption": caption,
                "parse_mode": "HTML"
            }
            
            # دانلود ویدیو
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as response:
                    if response.status == 200:
                        video_data = await response.read()
                        
                        files = {
                            "document": ("video.mp4", video_data, "video/mp4")
                        }
                        
                        response = requests.post(url, data=data, files=files, timeout=30)
                        return response.status_code == 200
        except Exception as e:
            print(f"Telegram video send error: {e}")
            return False

class SocialMediaScraper:
    def __init__(self):
        self.telegram = TelegramBotHandler(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.downloader = VideoDownloader()
        self.stats = {
            "total_downloads": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "last_run": None
        }
    
    async def scrape_tiktok_trending(self, limit: int = 10) -> List[Dict]:
        """اسکرپ ترندهای TikTok"""
        try:
            # در نسخه واقعی اینجا از API TikTok استفاده می‌شود
            videos = []
            for i in range(limit):
                video_data = {
                    'id': f'tiktok_{i}',
                    'description': f'ویدیوی ترند تیک‌تاک شماره {i+1} 🎵',
                    'views': 500000 + i * 25000,
                    'likes': 25000 + i * 1200,
                    'comments': 1500 + i * 80,
                    'platform': 'tiktok',
                    'hashtags': ['#ترند', '#تیک‌تاک', '#ویدیو', '#ایران'],
                    'url': f'https://www.tiktok.com/@creator/video/7{i}123456789',
                    'download_url': None,
                    'timestamp': datetime.now().isoformat()
                }
                
                # دریافت لینک دانلود
                download_url = await self.downloader.download_tiktok_no_watermark(video_data['url'])
                video_data['download_url'] = download_url
                
                if download_url:
                    self.stats["successful_downloads"] += 1
                    # ارسال به تلگرام
                    caption = self._create_caption(video_data)
                    await self.telegram.send_video(download_url, caption)
                else:
                    self.stats["failed_downloads"] += 1
                
                self.stats["total_downloads"] += 1
                videos.append(video_data)
            
            self.stats["last_run"] = datetime.now().isoformat()
            return videos
            
        except Exception as e:
            error_msg = f"❌ خطا در دریافت ترندهای تیک‌تاک: {str(e)}"
            self.telegram.send_message(error_msg)
            return []
    
    async def scrape_instagram_trending(self, limit: int = 10) -> List[Dict]:
        """اسکرپ ترندهای Instagram"""
        try:
            videos = []
            for i in range(limit):
                video_data = {
                    'id': f'instagram_{i}',
                    'description': f'پست ترند اینستاگرام شماره {i+1} 📸',
                    'views': 300000 + i * 15000,
                    'likes': 18000 + i * 900,
                    'comments': 800 + i * 40,
                    'platform': 'instagram',
                    'hashtags': ['#اینستاگرام', '#ترند', '#اکسپلور', '#پست'],
                    'url': f'https://www.instagram.com/p/ABC{i}123456/',
                    'download_url': None,
                    'timestamp': datetime.now().isoformat()
                }
                
                download_url = await self.downloader.download_instagram_no_watermark(video_data['url'])
                video_data['download_url'] = download_url
                
                if download_url:
                    self.stats["successful_downloads"] += 1
                    caption = self._create_caption(video_data)
                    await self.telegram.send_video(download_url, caption)
                else:
                    self.stats["failed_downloads"] += 1
                
                self.stats["total_downloads"] += 1
                videos.append(video_data)
            
            self.stats["last_run"] = datetime.now().isoformat()
            return videos
            
        except Exception as e:
            error_msg = f"❌ خطا در دریافت ترندهای اینستاگرام: {str(e)}"
            self.telegram.send_message(error_msg)
            return []
    
    def _create_caption(self, video_data: Dict) -> str:
        """ایجاد کپشن برای ویدیوها"""
        platform_icons = {
            'tiktok': '🎵',
            'instagram': '📸',
            'youtube': '🎥'
        }
        
        icon = platform_icons.get(video_data['platform'], '📹')
        hashtags = ' '.join(video_data.get('hashtags', [])[:3])
        
        return f"""
{icon} <b>{video_data['platform'].upper()} ترند</b>
────────────────────
📝 {video_data['description']}
👁️ {video_data['views']:,} بازدید
❤️ {video_data['likes']:,} لایک
💬 {video_data['comments']:,} کامنت
🔗 <a href="{video_data['url']}">لینک اصلی</a>

{hashtags}
"""
    
    async def download_custom_url(self, url: str) -> Dict:
        """دانلود از URL دلخواه"""
        try:
            download_url = await self.downloader.download_from_url(url)
            
            result = {
                "original_url": url,
                "download_url": download_url,
                "success": download_url is not None,
                "platform": self._detect_platform(url)
            }
            
            if download_url:
                caption = f"📥 ویدیو دانلود شده از {result['platform']}\n🔗 {url}"
                await self.telegram.send_video(download_url, caption)
                self.stats["successful_downloads"] += 1
            else:
                self.stats["failed_downloads"] += 1
            
            self.stats["total_downloads"] += 1
            return result
            
        except Exception as e:
            error_msg = f"❌ خطا در دانلود لینک: {str(e)}"
            self.telegram.send_message(error_msg)
            return {"success": False, "error": str(e)}
    
    def _detect_platform(self, url: str) -> str:
        """تشخیص پلتفرم از روی URL"""
        if 'tiktok.com' in url:
            return 'tiktok'
        elif 'instagram.com' in url:
            return 'instagram'
        elif 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        else:
            return 'unknown'
    
    def get_stats(self) -> Dict:
        """دریافت آمار عملکرد"""
        success_rate = 0
        if self.stats["total_downloads"] > 0:
            success_rate = (self.stats["successful_downloads"] / self.stats["total_downloads"]) * 100
        
        return {
            **self.stats,
            "success_rate": round(success_rate, 2),
            "uptime": "active"
        }

# Routes
@app.get("/")
async def root():
    return {
        "message": "🤖 ربات دانلود ویدیوهای ترند فعال است!",
        "version": "2.0",
        "endpoints": {
            "trending": "/trending/all",
            "download_tiktok": "/download/tiktok",
            "download_instagram": "/download/instagram", 
            "download_custom": "/download/custom?url=YOUR_URL",
            "stats": "/stats"
        }
    }

@app.get("/trending/all")
async def get_all_trending(limit: int = 5):
    """دریافت همه ترندها"""
    scraper = app.state.scraper
    tiktok = await scraper.scrape_tiktok_trending(limit)
    instagram = await scraper.scrape_instagram_trending(limit)
    
    total = len(tiktok) + len(instagram)
    successful = len([v for v in tiktok if v['download_url']]) + len([v for v in instagram if v['download_url']])
    
    # ارسال گزارش
    report = f"""
📊 <b>گزارش کامل ترندها</b>
────────────────────
🎵 TikTok: {len(tiktok)} ویدیو
📸 Instagram: {len(instagram)} پست
✅ موفق: {successful} از {total}
📅 {datetime.now().strftime('%Y/%m/%d %H:%M')}
"""
    scraper.telegram.send_message(report)
    
    return {
        "tiktok": {"count": len(tiktok), "videos": tiktok},
        "instagram": {"count": len(instagram), "videos": instagram},
        "total": total,
        "successful": successful
    }

@app.get("/download/tiktok")
async def download_tiktok(limit: int = 5):
    """دانلود ترندهای TikTok"""
    scraper = app.state.scraper
    videos = await scraper.scrape_tiktok_trending(limit)
    return {
        "platform": "tiktok",
        "count": len(videos),
        "successful": len([v for v in videos if v['download_url']]),
        "videos": videos
    }

@app.get("/download/instagram")
async def download_instagram(limit: int = 5):
    """دانلود ترندهای Instagram"""
    scraper = app.state.scraper
    videos = await scraper.scrape_instagram_trending(limit)
    return {
        "platform": "instagram", 
        "count": len(videos),
        "successful": len([v for v in videos if v['download_url']]),
        "videos": videos
    }

@app.get("/download/custom")
async def download_custom_url(url: str):
    """دانلود از URL دلخواه"""
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
    
    scraper = app.state.scraper
    result = await scraper.download_custom_url(url)
    return result

@app.get("/stats")
async def get_stats():
    """دریافت آمار عملکرد"""
    scraper = app.state.scraper
    stats = scraper.get_stats()
    return stats

@app.get("/test")
async def test_bot():
    """تست سلامت ربات"""
    scraper = app.state.scraper
    success = scraper.telegram.send_message(f"""
✅ <b>تست سلامت ربات</b>
────────────────────
🤖 وضعیت: <b>فعال</b>
⏰ زمان: {datetime.now().strftime('%Y/%m/%d %H:%M')}
📡 سرویس: <b>آنلاین</b>
────────────────────
ربات آماده دریافت فرمان‌ها است!
""")
    return {"status": "success" if success else "failed", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
