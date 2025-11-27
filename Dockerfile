FROM python:3.11-slim

# استفاده از نسخه پایدارتر Debian
FROM python:3.11-bullseye

# نصب وابستگی‌های سیستم برای Playwright و FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    gnupg \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm-dev \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    fonts-liberation \
    libappindicator3-1 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# ایجاد دایرکتوری کاری
WORKDIR /app

# کپی فایل requirements
COPY requirements.txt .

# نصب پکیج‌های پایتون
RUN pip install --no-cache-dir -r requirements.txt

# نصب Playwright و مرورگر - بدون install-deps
RUN pip install playwright
RUN playwright install chromium

# کپی تمام فایل‌های پروژه
COPY . .

# دستور اجرا
CMD ["python", "main.py"]
