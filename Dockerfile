FROM python:3.12

RUN mkdir -p /usr/src/app

WORKDIR /usr/src/app

COPY . .

EXPOSE 3000

CMD ["python", "main.py"]