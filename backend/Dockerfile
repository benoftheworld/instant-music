FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN DEBIAN_FRONTEND=noninteractive apt-get update -qq && \
    apt-get install -qq -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt /app/requirements/base.txt
COPY requirements/development.txt /app/requirements/development.txt
RUN pip install -q --upgrade pip && pip install -q -r /app/requirements/development.txt

COPY . /app/

RUN mkdir -p /app/staticfiles /app/media

EXPOSE 8000

# Use uvicorn ASGI server in development for faster async handling and reloads
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload", "--proxy-headers", "--loop", "uvloop", "--http", "h11"]