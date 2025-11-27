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
from instagrapi import Client
from instagrapi.exceptions import LoginRequired

# ایجاد lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup events
    print("🚀 Starting Instagram Scraper with Instagrapi...")
    
    # ایجاد نمونه‌ها
    app.state.scraper = InstagramScraper()
    
    # ارسال پیام راه‌اندازی
    app.state.scraper.telegram.send_message(f"""
🚀 <b>ربات Instagram Scraper راه‌اندازی شد</b>
────────────────────
🤖 Instagram Scraper v1.0
📅 {datetime.now().strftime('%Y/%m/%d %H:%M')}
📍 سرور: Railway
🔧 کتابخانه: <b>Instagrapi</b>
✅ وضعیت: <b>فعال</b>
────────────────────
آماده دریافت پست‌های ترند اینستاگرام!
""")
    
    yield
    
    # Shutdown events
    print("🔴 Shutting down Instagram Scraper...")
    app.state.scraper.telegram.send_message("🔴 ربات متوقف شد")

# ایجاد FastAPI با lifespan
app = FastAPI(title="Instagram Scraper", version="1.0", lifespan=lifespan)

# Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8361557378:AAEntX7ri-he2foBASD4JPGvfSzBLMS3Spg")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5800900434")
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")

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
            print(f"❌ Telegram send error: {e}")
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
            
            print(f"📤 Sending video to Telegram: {video_url}")
            
            # دانلود ویدیو
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as response:
                    if response.status == 200:
                        video_data = await response.read()
                        
                        files = {
                            "document": ("video.mp4", video_data, "video/mp4")
                        }
                        
                        response = requests.post(url, data=data, files=files, timeout=60)
                        if response.status_code == 200:
                            print("✅ Video sent to Telegram successfully")
                            return True
                        else:
                            print(f"❌ Telegram API error: {response.status_code}")
                            return False
        except Exception as e:
            print(f"❌ Telegram video send error: {e}")
            return False
    
    async def send_photo(self, photo_url: str, caption: str = "") -> bool:
        """ارسال عکس به تلگرام"""
        if not photo_url:
            return False
        
        try:
            url = f"{self.base_url}/sendPhoto"
            data = {
                "chat_id": self.chat_id,
                "caption": caption,
                "parse_mode": "HTML"
            }
            
            files = {
                "photo": ("photo.jpg", requests.get(photo_url).content, "image/jpeg")
            }
            
            response = requests.post(url, data=data, files=files, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Telegram photo send error: {e}")
            return False

class InstagramScraper:
    def __init__(self):
        self.telegram = TelegramBotHandler(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.cl = Client()
        self.stats = {
            "total_downloads": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "last_run": None
        }
        
        # تلاش برای login اگر اطلاعات موجود باشد
        if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
            try:
                self.cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                print("✅ Successfully logged into Instagram")
                self.telegram.send_message("✅ <b>اتصال به اینستاگرام با موفقیت انجام شد</b>")
            except Exception as e:
                print(f"❌ Instagram login failed: {e}")
                self.telegram.send_message("❌ <b>خطا در اتصال به اینستاگرام</b>\n\nربات با حساب عمومی کار خواهد کرد.")
        else:
            print("ℹ️ No Instagram credentials provided - using public mode")
            self.telegram.send_message("ℹ️ <b>حالت عمومی فعال شد</b>\n\nربات فقط به محتوای عمومی دسترسی دارد.")
    
    async def get_trending_hashtags(self, limit=10) -> List[Dict]:
        """دریافت پست‌های ترند از هشتگ‌های محبوب"""
        try:
            print("🔄 Getting trending posts from Instagram...")
            
            # هشتگ‌های ترند
            trending_hashtags = [
                "trending", "viral", "popular", "explore", 
                "fashion", "music", "art", "travel", "food"
            ]
            
            all_posts = []
            
            for hashtag in trending_hashtags[:3]:  # فقط 3 هشتگ برای تست
                try:
                    print(f"🔍 Searching hashtag: #{hashtag}")
                    
                    # دریافت پست‌های برتر از هشتگ
                    posts = self.cl.hashtag_medias_top(hashtag, amount=limit)
                    
                    for post in posts:
                        post_data = await self._process_instagram_post(post)
                        if post_data:
                            all_posts.append(post_data)
                            
                except Exception as e:
                    print(f"❌ Error with hashtag #{hashtag}: {e}")
                    continue
            
            # حذف duplicates بر اساس post ID
            unique_posts = {post['id']: post for post in all_posts}.values()
            posts_list = list(unique_posts)[:limit]
            
            self.stats["last_run"] = datetime.now().isoformat()
            print(f"✅ Found {len(posts_list)} unique trending posts")
            
            return list(posts_list)
            
        except Exception as e:
            error_msg = f"❌ خطا در دریافت ترندهای اینستاگرام: {str(e)}"
            print(error_msg)
            self.telegram.send_message(error_msg)
            return []
    
    async def _process_instagram_post(self, post) -> Optional[Dict]:
        """پردازش پست اینستاگرام و ارسال به تلگرام"""
        try:
            post_data = {
                'id': post.id,
                'description': post.caption_text[:200] + "..." if post.caption_text and len(post.caption_text) > 200 else post.caption_text or "پست اینستاگرام",
                'likes': post.like_count,
                'comments': post.comment_count,
                'views': post.video_view_count if post.media_type == 2 else 0,
                'platform': 'instagram',
                'hashtags': self._extract_hashtags(post.caption_text or ""),
                'url': f"https://instagram.com/p/{post.code}",
                'media_type': post.media_type,  # 1: عکس, 2: ویدیو, 8: album
                'download_url': None,
                'timestamp': datetime.now().isoformat()
            }
            
            # تشخیص نوع مدیا و دریافت لینک دانلود
            if post.media_type == 1:  # عکس
                post_data['download_url'] = post.thumbnail_url
            elif post.media_type == 2:  # ویدیو
                post_data['download_url'] = post.video_url
            elif post.media_type == 8:  # آلبوم
                post_data['download_url'] = post.thumbnail_url  # اولین عکس
            
            # ارسال به تلگرام
            if post_data['download_url']:
                caption = self._create_caption(post_data)
                
                if post.media_type == 2:  # ویدیو
                    success = await self.telegram.send_video(post_data['download_url'], caption)
                else:  # عکس
                    success = await self.telegram.send_photo(post_data['download_url'], caption)
                
                if success:
                    self.stats["successful_downloads"] += 1
                    print(f"✅ Successfully sent post {post.id} to Telegram")
                else:
                    self.stats["failed_downloads"] += 1
                    print(f"❌ Failed to send post {post.id} to Telegram")
            else:
                self.stats["failed_downloads"] += 1
                print(f"❌ No download URL for post {post.id}")
            
            self.stats["total_downloads"] += 1
            return post_data
            
        except Exception as e:
            print(f"❌ Error processing post: {e}")
            return None
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """استخراج هشتگ‌ها از متن"""
        return re.findall(r'#\w+', text) if text else []
    
    def _create_caption(self, post_data: Dict) -> str:
        """ایجاد کپشن برای پست"""
        media_types = {
            1: "📸 عکس",
            2: "🎥 ویدیو", 
            8: "🖼️ آلبوم"
        }
        
        media_type = media_types.get(post_data['media_type'], "📄 پست")
        hashtags = ' '.join(post_data.get('hashtags', [])[:3])
        
        return f"""
{media_type} <b>اینستاگرام ترند</b>
────────────────────
📝 {post_data['description']}
❤️ {post_data['likes']:,} لایک
💬 {post_data['comments']:,} کامنت
👁️ {post_data['views']:,} بازدید
🔗 <a href="{post_data['url']}">لینک اصلی</a>

{hashtags}
"""
    
    async def download_by_username(self, username: str, limit: int = 5) -> List[Dict]:
        """دریافت پست‌های یک کاربر"""
        try:
            user_id = self.cl.user_id_from_username(username)
            posts = self.cl.user_medias(user_id, amount=limit)
            
            results = []
            for post in posts:
                post_data = await self._process_instagram_post(post)
                if post_data:
                    results.append(post_data)
            
            return results
        except Exception as e:
            error_msg = f"❌ خطا در دریافت پست‌های کاربر {username}: {str(e)}"
            self.telegram.send_message(error_msg)
            return []
    
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
        "message": "🤖 ربات اینستاگرام اسکرپر فعال است!",
        "version": "1.0",
        "endpoints": {
            "trending": "/trending",
            "user_posts": "/user/{username}",
            "stats": "/stats",
            "test": "/test"
        }
    }

@app.get("/trending")
async def get_trending(limit: int = 5):
    """دریافت پست‌های ترند اینستاگرام"""
    scraper = app.state.scraper
    posts = await scraper.get_trending_hashtags(limit)
    
    # ارسال گزارش
    successful = len([p for p in posts if p.get('download_url')])
    report = f"""
📊 <b>گزارش ترندهای اینستاگرام</b>
────────────────────
📸 تعداد پست‌ها: <b>{len(posts)}</b>
✅ موفق: <b>{successful}</b>
📅 {datetime.now().strftime('%Y/%m/%d %H:%M')}
"""
    scraper.telegram.send_message(report)
    
    return {
        "platform": "instagram",
        "count": len(posts),
        "successful": successful,
        "posts": posts
    }

@app.get("/user/{username}")
async def get_user_posts(username: str, limit: int = 5):
    """دریافت پست‌های یک کاربر"""
    scraper = app.state.scraper
    posts = await scraper.download_by_username(username, limit)
    
    return {
        "username": username,
        "count": len(posts),
        "posts": posts
    }

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
✅ <b>تست سلامت ربات اینستاگرام</b>
────────────────────
🤖 وضعیت: <b>فعال</b>
⏰ زمان: {datetime.now().strftime('%Y/%m/%d %H:%M')}
📡 سرویس: <b>Instagrapi</b>
🔧 نسخه: 1.0
────────────────────
ربات آماده دریافت پست‌های ترند اینستاگرام!
""")
    return {"status": "success" if success else "failed", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
