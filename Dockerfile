FROM python:3.12-alpine as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update && apk add git build-base

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

RUN apk del git build-base


FROM python:3.12-alpine

COPY --from=builder /app/wheels /wheels

RUN apk update && apk add ffmpeg aria2
RUN pip install --no-cache /wheels/*

COPY static static

COPY bot bot

CMD python bot/main.py
