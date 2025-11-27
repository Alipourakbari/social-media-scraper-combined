FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نصب Playwright بدون مرورگر (سبک‌تر)
RUN pip install playwright

COPY . .

CMD ["python", "main.py"]
