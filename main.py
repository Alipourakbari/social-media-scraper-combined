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
from playwright.async_api import async_playwright

# ایجاد lifespan manager اول
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup events
    print("🚀 Starting Social Media Scraper with Real Web Scraping...")
    
    # ایجاد نمونه‌ها
    app.state.scraper = SocialMediaScraper()
    
    # ارسال پیام راه‌اندازی
    app.state.scraper.telegram.send_message("""
🚀 <b>ربات راه‌اندازی شد - نسخه Web Scraping</b>
────────────────────
🤖 Social Media Scraper v4.0
📅 {datetime.now().strftime('%Y/%m/%d %H:%M')}
📍 سرور: Railway
🔧 حالت: <b>Web Scraping مستقیم</b>
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
app = FastAPI(title="Social Media Scraper - Web Scraping", version="4.0", lifespan=lifespan)

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
                            print(f"🎯 API Response from {api_url}: {data}")
                            
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
                                print(f"✅ Download URL found: {download_url}")
                                return download_url
                except Exception as e:
                    print(f"❌ API {api_url} failed: {e}")
                    continue
            
            print("❌ No working API found for TikTok")
            return None
        except Exception as e:
            print(f"❌ TikTok download error: {e}")
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
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                    
                    async with session.get(api_url, headers=headers, timeout=15) as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"🎯 Instagram API Response: {data}")
                            
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
                    print(f"❌ Instagram API {api_url} failed: {e}")
                    continue
            
            print("❌ No working API found for Instagram")
            return None
        except Exception as e:
            print(f"❌ Instagram download error: {e}")
            return None
    
    async def download_from_url(self, url: str) -> Optional[str]:
        """دانلود از هر URL با تشخیص خودکار پلتفرم"""
        print(f"🔍 Attempting to download from: {url}")
        
        if 'tiktok.com' in url:
            return await self.download_tiktok_no_watermark(url)
        elif 'instagram.com' in url:
            return await self.download_instagram_no_watermark(url)
        elif 'youtube.com/shorts' in url or 'youtu.be' in url:
            return await self.download_youtube_shorts(url)
        else:
            print(f"❌ Unsupported platform for URL: {url}")
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
    
    async def scrape_tiktok_trending_direct(self) -> List[Dict]:
        """اسکرپ مستقیم TikTok با Playwright"""
        try:
            print("🔄 Starting TikTok direct scraping with Playwright...")
            videos = []
            
            async with async_playwright() as p:
                # استفاده از Chromium با تنظیمات خاص برای Railway
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--no-first-run',
                        '--no-zygote',
                        '--single-process'
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                
                page = await context.new_page()
                
                try:
                    print("🌐 Navigating to TikTok...")
                    
                    # رفتن به صفحه TikTok
                    await page.goto('https://www.tiktok.com', timeout=60000)
                    await page.wait_for_timeout(5000)
                    
                    print("✅ TikTok page loaded")
                    
                    # جستجو برای ویدیوهای ترند
                    await page.goto('https://www.tiktok.com/search/video?q=trending', timeout=60000)
                    await page.wait_for_timeout(5000)
                    
                    # اسکرپ ویدیوها
                    video_selectors = [
                        'div[data-e2e="search-card"]',
                        'div.tiktok-x6y88p-DivItemContainerV2',
                        'div[class*="DivItemContainer"]',
                        'div[data-e2e="recommend-list-item-container"]'
                    ]
                    
                    for selector in video_selectors:
                        video_elements = await page.query_selector_all(selector)
                        if video_elements:
                            print(f"✅ Found {len(video_elements)} videos with selector: {selector}")
                            break
                    
                    if not video_elements:
                        # اگر ویدیویی پیدا نشد، از صفحه اصلی اسکرپ کنیم
                        await page.goto('https://www.tiktok.com/foryou', timeout=60000)
                        await page.wait_for_timeout(5000)
                        video_elements = await page.query_selector_all('div[class*="DivItemContainer"]')
                    
                    for i, element in enumerate(video_elements[:3]):  # فقط 3 ویدیو برای تست
                        try:
                            print(f"🔍 Processing video {i+1}...")
                            
                            # پیدا کردن لینک ویدیو
                            link_element = await element.query_selector('a')
                            if link_element:
                                video_path = await link_element.get_attribute('href')
                                if video_path and '/video/' in video_path:
                                    video_url = f"https://www.tiktok.com{video_path}"
                                    
                                    print(f"🎯 Found video URL: {video_url}")
                                    
                                    video_data = {
                                        'id': f'tiktok_direct_{i}',
                                        'description': f'ویدیوی ترند TikTok #{i+1}',
                                        'views': 100000 * (i + 1),
                                        'likes': 5000 * (i + 1),
                                        'comments': 200 * (i + 1),
                                        'platform': 'tiktok',
                                        'hashtags': ['#ترند', '#تيك_توك', '#ویدیو'],
                                        'url': video_url,
                                        'download_url': None,
                                        'timestamp': datetime.now().isoformat()
                                    }
                                    
                                    # دانلود ویدیو
                                    print(f"📥 Downloading video {i+1}...")
                                    download_url = await self.downloader.download_tiktok_no_watermark(video_url)
                                    video_data['download_url'] = download_url
                                    
                                    if download_url:
                                        print(f"✅ Video {i+1} downloaded successfully")
                                        self.stats["successful_downloads"] += 1
                                        
                                        # ارسال به تلگرام
                                        caption = self._create_caption(video_data)
                                        await self.telegram.send_video(download_url, caption)
                                    else:
                                        print(f"❌ Failed to download video {i+1}")
                                        self.stats["failed_downloads"] += 1
                                    
                                    self.stats["total_downloads"] += 1
                                    videos.append(video_data)
                                    
                        except Exception as e:
                            print(f"❌ Error processing video {i}: {e}")
                            continue
                    
                except Exception as e:
                    print(f"❌ TikTok scraping error: {e}")
                
                finally:
                    await browser.close()
            
            print(f"✅ TikTok scraping completed: {len(videos)} videos processed")
            return videos
            
        except Exception as e:
            print(f"❌ TikTok direct scraping error: {e}")
            return []
    
    async def scrape_instagram_trending_direct(self) -> List[Dict]:
        """اسکرپ مستقیم Instagram با Playwright"""
        try:
            print("🔄 Starting Instagram direct scraping with Playwright...")
            videos = []
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage'
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                
                page = await context.new_page()
                
                try:
                    print("🌐 Navigating to Instagram...")
                    
                    # رفتن به صفحه اکسپلور Instagram
                    await page.goto('https://www.instagram.com/explore/', timeout=60000)
                    await page.wait_for_timeout(5000)
                    
                    print("✅ Instagram explore page loaded")
                    
                    # اسکرپ پست‌ها
                    post_selectors = [
                        'article div._aabd',
                        'div[role="button"] div._aagv',
                        'div._aabd'
                    ]
                    
                    post_elements = []
                    for selector in post_selectors:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            post_elements = elements
                            print(f"✅ Found {len(elements)} posts with selector: {selector}")
                            break
                    
                    for i, element in enumerate(post_elements[:3]):  # فقط 3 پست برای تست
                        try:
                            print(f"🔍 Processing Instagram post {i+1}...")
                            
                            # کلیک روی پست برای گرفتن لینک
                            await element.click()
                            await page.wait_for_timeout(2000)
                            
                            # گرفتن لینک پست از URL
                            current_url = page.url
                            if '/p/' in current_url:
                                post_url = current_url.split('?')[0]  # حذف پارامترها
                                
                                print(f"🎯 Found Instagram post URL: {post_url}")
                                
                                post_data = {
                                    'id': f'instagram_direct_{i}',
                                    'description': f'پست ترند Instagram #{i+1}',
                                    'views': 50000 * (i + 1),
                                    'likes': 3000 * (i + 1),
                                    'comments': 150 * (i + 1),
                                    'platform': 'instagram',
                                    'hashtags': ['#اینستاگرام', '#ترند', '#اکسپلور'],
                                    'url': post_url,
                                    'download_url': None,
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                                # دانلود ویدیو/عکس
                                print(f"📥 Downloading Instagram post {i+1}...")
                                download_url = await self.downloader.download_instagram_no_watermark(post_url)
                                post_data['download_url'] = download_url
                                
                                if download_url:
                                    print(f"✅ Instagram post {i+1} downloaded successfully")
                                    self.stats["successful_downloads"] += 1
                                    
                                    # ارسال به تلگرام
                                    caption = self._create_caption(post_data)
                                    await self.telegram.send_video(download_url, caption)
                                else:
                                    print(f"❌ Failed to download Instagram post {i+1}")
                                    self.stats["failed_downloads"] += 1
                                
                                self.stats["total_downloads"] += 1
                                videos.append(post_data)
                            
                            # برگشت به صفحه اکسپلور
                            await page.go_back()
                            await page.wait_for_timeout(1000)
                            
                        except Exception as e:
                            print(f"❌ Error processing Instagram post {i}: {e}")
                            continue
                    
                except Exception as e:
                    print(f"❌ Instagram scraping error: {e}")
                
                finally:
                    await browser.close()
            
            print(f"✅ Instagram scraping completed: {len(videos)} posts processed")
            return videos
            
        except Exception as e:
            print(f"❌ Instagram direct scraping error: {e}")
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
            print(f"🔍 Downloading custom URL: {url}")
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
        "message": "🤖 ربات دانلود ویدیوهای ترند با Web Scraping فعال است!",
        "version": "4.0",
        "endpoints": {
            "trending_direct": "/trending/direct",
            "download_custom": "/download/custom?url=YOUR_URL",
            "stats": "/stats",
            "test": "/test"
        }
    }

@app.get("/trending/direct")
async def get_direct_trending():
    """دریافت ترندهای مستقیم با Web Scraping"""
    scraper = app.state.scraper
    
    print("🚀 Starting direct trending scraping...")
    
    # اسکرپ TikTok و Instagram به صورت موازی
    tiktok_task = asyncio.create_task(scraper.scrape_tiktok_trending_direct())
    instagram_task = asyncio.create_task(scraper.scrape_instagram_trending_direct())
    
    tiktok = await tiktok_task
    instagram = await instagram_task
    
    total = len(tiktok) + len(instagram)
    successful = len([v for v in tiktok if v['download_url']]) + len([v for v in instagram if v['download_url']])
    
    # ارسال گزارش
    report = f"""
📊 <b>گزارش Web Scraping مستقیم</b>
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
        "successful": successful,
        "scraping_method": "direct_playwright"
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
✅ <b>تست سلامت ربات - نسخه Web Scraping</b>
────────────────────
🤖 وضعیت: <b>فعال</b>
⏰ زمان: {datetime.now().strftime('%Y/%m/%d %H:%M')}
📡 سرویس: <b>Web Scraping مستقیم</b>
🔧 نسخه: 4.0
────────────────────
ربات آماده دریافت فرمان‌ها است!
""")
    return {"status": "success" if success else "failed", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
