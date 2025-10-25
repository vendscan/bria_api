FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

CMD python -m uvicorn main:app --host 0.0.0.0 --port ${PORT}
