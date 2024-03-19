FROM python:3.12

RUN mkdir -p /app

WORKDIR /app

COPY . .

EXPOSE 3000

CMD ["python", "main.py"]