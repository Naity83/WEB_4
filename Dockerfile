FROM python:3.12

RUN mkdir -p /usr/src/app

WORKDIR /usr/src/app

COPY . .

RUN mkdir -p storage && touch storage/data.json

EXPOSE 3000

CMD ["python", "main.py"]