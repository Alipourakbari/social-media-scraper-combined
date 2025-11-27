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
    print("🚀 Starting Social Media Scraper with Real APIs...")
    
    # ایجاد نمونه‌ها
    app.state.scraper = SocialMediaScraper()
    
    # ارسال پیام راه‌اندازی
    app.state.scraper.telegram.send_message("""
🚀 <b>ربات راه‌اندازی شد - نسخه Real API</b>
────────────────────
🤖 Social Media Scraper v3.0
📅 {datetime.now().strftime('%Y/%m/%d %H:%M')}
📍 سرور: Railway
🔧 حالت: <b>APIهای واقعی</b>
✅ وضعیت: <b>فعال</b>
────────────────────
آماده دریافت ترندهای واقعی و دانلود ویدیو!
""")
    
    yield  # اینجا برنامه اجرا می‌شود
    
    # Shutdown events
    print("🔴 Shutting down Social Media Scraper...")
    await app.state.scraper.downloader.close_session()
    app.state.scraper.telegram.send_message("🔴 ربات متوقف شد")

# ایجاد FastAPI با lifespan
app = FastAPI(title="Social Media Scraper - Real APIs", version="3.0", lifespan=lifespan)

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
        """دانلود ویدیو TikTok بدون واترمارک با APIهای واقعی"""
        try:
            session = await self.get_session()
            
            # لیست APIهای واقعی و فعال
            apis = [
                f"https://www.tikwm.com/api/?url={video_url}",
                f"https://tikdown.org/api?url={video_url}",
                f"https://api.tiklydown.eu.org/api/download?url={video_url}",
                f"https://tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com/vid/index?url={video_url}"
            ]
            
            for api_url in apis:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                    
                    async with session.get(api_url, headers=headers, timeout=15) as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"API Response: {data}")  # برای دیباگ
                            
                            # استخراج لینک دانلود از فرمت‌های مختلف
                            download_url = (
                                data.get('data', {}).get('play') or
                                data.get('data', {}).get('wmplay') or
                                data.get('data', {}).get('hdplay') or
                                data.get('url') or
                                data.get('videoUrl') or
                                data.get('download_url')
                            )
                            
                            if download_url:
                                if not download_url.startswith('http'):
                                    download_url = 'https:' + download_url
                                print(f"Download URL found: {download_url}")
                                return download_url
                except Exception as e:
                    print(f"API {api_url} failed: {e}")
                    continue
            
            print("No working API found for TikTok")
            return None
        except Exception as e:
            print(f"TikTok download error: {e}")
            return None
    
    async def download_instagram_no_watermark(self, post_url: str) -> Optional[str]:
        """دانلود ویدیو اینستاگرام بدون واترمارک با APIهای واقعی"""
        try:
            session = await self.get_session()
            
            apis = [
                f"https://instasupersave.com/api/ig?url={post_url}",
                f"https://igram.io/api/ig?url={post_url}",
                f"https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index?url={post_url}"
            ]
            
            for api_url in apis:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                    
                    async with session.get(api_url, headers=headers, timeout=15) as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"Instagram API Response: {data}")
                            
                            # استخراج لینک از فرمت‌های مختلف
                            if isinstance(data, dict):
                                if data.get('links'):
                                    for link in data['links']:
                                        if link.get('quality') in ['hd', 'sd', 'high', 'medium']:
                                            return link['url']
                                elif data.get('url'):
                                    return data['url']
                                elif data.get('media'):
                                    return data['media']
                except Exception as e:
                    print(f"Instagram API {api_url} failed: {e}")
                    continue
            
            print("No working API found for Instagram")
            return None
        except Exception as e:
            print(f"Instagram download error: {e}")
            return None
    
    async def download_youtube_shorts(self, video_url: str) -> Optional[str]:
        """دانلود YouTube Shorts با APIهای واقعی"""
        try:
            session = await self.get_session()
            
            apis = [
                f"https://co.wuk.sh/api/json",
                f"https://yt5s.com/en/api/convert",
            ]
            
            for api_url in apis:
                try:
                    headers = {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                    
                    payload = {
                        'url': video_url,
                        'format': 'mp4'
                    }
                    
                    async with session.post(api_url, json=payload, headers=headers, timeout=20) as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"YouTube API Response: {data}")
                            
                            return data.get('url') or data.get('downloadUrl') or data.get('link')
                except Exception as e:
                    print(f"YouTube API {api_url} failed: {e}")
                    continue
            
            return None
        except Exception as e:
            print(f"YouTube download error: {e}")
            return None
    
    async def download_from_url(self, url: str) -> Optional[str]:
        """دانلود از هر URL با تشخیص خودکار پلتفرم"""
        print(f"Attempting to download from: {url}")
        
        if 'tiktok.com' in url:
            return await self.download_tiktok_no_watermark(url)
        elif 'instagram.com' in url:
            return await self.download_instagram_no_watermark(url)
        elif 'youtube.com/shorts' in url or 'youtu.be' in url:
            return await self.download_youtube_shorts(url)
        else:
            print(f"Unsupported platform for URL: {url}")
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
                        
                        response = requests.post(url, data=data, files=files, timeout=60)
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
    
    async def get_real_trending_videos(self) -> Dict[str, List[Dict]]:
        """دریافت ترندهای واقعی از APIهای عمومی"""
        try:
            # استفاده از APIهای عمومی برای ترندها
            trending_data = {
                "tiktok": await self._get_tiktok_trending_from_api(),
                "instagram": await self._get_instagram_trending_from_api()
            }
            
            return trending_data
        except Exception as e:
            error_msg = f"❌ خطا در دریافت ترندهای واقعی: {str(e)}"
            self.telegram.send_message(error_msg)
            return {"tiktok": [], "instagram": []}
    
    async def _get_tiktok_trending_from_api(self) -> List[Dict]:
        """دریافت ترندهای واقعی TikTok از API"""
        try:
            # استفاده از API عمومی TikTok برای ترندها
            async with aiohttp.ClientSession() as session:
                # این API ترندهای TikTok رو برمی‌گردونه
                api_url = "https://tiktok-api-fetcher.vercel.app/api/trending"
                
                async with session.get(api_url, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        videos = []
                        
                        for item in data.get('videos', [])[:10]:  # 10 ویدیوی اول
                            video_data = {
                                'id': item.get('id', ''),
                                'description': item.get('desc', 'ترند TikTok'),
                                'views': item.get('playCount', 0),
                                'likes': item.get('diggCount', 0),
                                'comments': item.get('commentCount', 0),
                                'platform': 'tiktok',
                                'hashtags': self._extract_hashtags(item.get('desc', '')),
                                'url': f"https://www.tiktok.com/@{item.get('author', {}).get('uniqueId', 'user')}/video/{item.get('id', '')}",
                                'download_url': None,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            # سعی در دانلود ویدیو
                            download_url = await self.downloader.download_tiktok_no_watermark(video_data['url'])
                            video_data['download_url'] = download_url
                            
                            if download_url:
                                self.stats["successful_downloads"] += 1
                                caption = self._create_caption(video_data)
                                await self.telegram.send_video(download_url, caption)
                            else:
                                self.stats["failed_downloads"] += 1
                            
                            self.stats["total_downloads"] += 1
                            videos.append(video_data)
                        
                        return videos
            
            return []
        except Exception as e:
            print(f"TikTok trending API error: {e}")
            return []
    
    async def _get_instagram_trending_from_api(self) -> List[Dict]:
        """دریافت ترندهای واقعی Instagram"""
        try:
            # استفاده از API عمومی برای ترندهای Instagram
            async with aiohttp.ClientSession() as session:
                # این API پست‌های پرطرفدار Instagram رو برمی‌گردونه
                api_url = "https://www.instagram.com/explore/tags/trending/?__a=1"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                async with session.get(api_url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = []
                        
                        # استخراج پست‌ها از پاسخ API
                        edges = data.get('graphql', {}).get('hashtag', {}).get('edge_hashtag_to_top_posts', {}).get('edges', [])
                        
                        for edge in edges[:10]:  # 10 پست اول
                            node = edge.get('node', {})
                            post_data = {
                                'id': node.get('id', ''),
                                'description': node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', 'ترند Instagram'),
                                'views': node.get('video_view_count', 0),
                                'likes': node.get('edge_liked_by', {}).get('count', 0),
                                'comments': node.get('edge_media_to_comment', {}).get('count', 0),
                                'platform': 'instagram',
                                'hashtags': self._extract_hashtags(node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', '')),
                                'url': f"https://www.instagram.com/p/{node.get('shortcode', '')}/",
                                'download_url': None,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            # سعی در دانلود ویدیو
                            download_url = await self.downloader.download_instagram_no_watermark(post_data['url'])
                            post_data['download_url'] = download_url
                            
                            if download_url:
                                self.stats["successful_downloads"] += 1
                                caption = self._create_caption(post_data)
                                await self.telegram.send_video(download_url, caption)
                            else:
                                self.stats["failed_downloads"] += 1
                            
                            self.stats["total_downloads"] += 1
                            posts.append(post_data)
                        
                        return posts
            
            return []
        except Exception as e:
            print(f"Instagram trending API error: {e}")
            return []
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """استخراج هشتگ‌ها از متن"""
        return re.findall(r'#\w+', text) if text else []
    
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
📝 {video_data['description'][:100]}{'...' if len(video_data['description']) > 100 else ''}
👁️ {video_data['views']:,} بازدید
❤️ {video_data['likes']:,} لایک
💬 {video_data['comments']:,} کامنت
🔗 <a href="{video_data['url']}">لینک اصلی</a>

{hashtags}
"""
    
    async def download_custom_url(self, url: str) -> Dict:
        """دانلود از URL دلخواه"""
        try:
            print(f"Downloading custom URL: {url}")
            download_url = await self.downloader.download_from_url(url)
            
            result = {
                "original_url": url,
                "download_url": download_url,
                "success": download_url is not None,
                "platform": self._detect_platform(url)
            }
            
            if download_url:
                caption = f"📥 ویدیو دانلود شده از {result['platform']}\n🔗 {url}"
                success = await self.telegram.send_video(download_url, caption)
                if success:
                    self.stats["successful_downloads"] += 1
                    result['telegram_sent'] = True
                else:
                    result['telegram_sent'] = False
            else:
                self.stats["failed_downloads"] += 1
                result['telegram_sent'] = False
            
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
        "message": "🤖 ربات دانلود ویدیوهای ترند با APIهای واقعی فعال است!",
        "version": "3.0",
        "endpoints": {
            "trending": "/trending/real",
            "download_tiktok": "/download/tiktok",
            "download_instagram": "/download/instagram", 
            "download_custom": "/download/custom?url=YOUR_URL",
            "stats": "/stats"
        }
    }

@app.get("/trending/real")
async def get_real_trending(limit: int = 5):
    """دریافت ترندهای واقعی"""
    scraper = app.state.scraper
    trending_data = await scraper.get_real_trending_videos()
    
    tiktok = trending_data.get('tiktok', [])[:limit]
    instagram = trending_data.get('instagram', [])[:limit]
    
    total = len(tiktok) + len(instagram)
    successful = len([v for v in tiktok if v['download_url']]) + len([v for v in instagram if v['download_url']])
    
    # ارسال گزارش
    report = f"""
📊 <b>گزارش ترندهای واقعی</b>
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
✅ <b>تست سلامت ربات - نسخه Real API</b>
────────────────────
🤖 وضعیت: <b>فعال</b>
⏰ زمان: {datetime.now().strftime('%Y/%m/%d %H:%M')}
📡 سرویس: <b>APIهای واقعی</b>
🔧 نسخه: 3.0
────────────────────
ربات آماده دریافت فرمان‌ها است!
""")
    return {"status": "success" if success else "failed", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
