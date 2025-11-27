FROM python:3.11-slim

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
    libxi6 \
    libxtst6 \
    libxrender1 \
    libxss1 \
    libnss3-tools \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# ایجاد دایرکتوری کاری
WORKDIR /app

# کپی فایل requirements
COPY requirements.txt .

# نصب پکیج‌های پایتون
RUN pip install --no-cache-dir -r requirements.txt

# نصب Playwright و مرورگر
RUN pip install playwright
RUN playwright install chromium
RUN playwright install-deps

# کپی تمام فایل‌های پروژه
COPY . .

# ایجاد کاربر غیر root برای امنیت
RUN useradd -m -u 1000 user
USER user

# دستور اجرا
CMD ["python", "main.py"]
