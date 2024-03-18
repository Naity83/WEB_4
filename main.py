import mimetypes
import urllib.parse
import json
import logging
import socket
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from datetime import datetime

BASE_DIR = Path()  # Установка BASE_DIR в текущую директорию
BUFFER_SIZE = 1024  # Установка BUFFER_SIZE для размера буфера сокета
HTTP_PORT = 3000  # Установка HTTP_PORT для порта HTTP-сервера
HTTP_HOST = '0.0.0.0'  # Установка HTTP_HOST для хоста HTTP-сервера
SOCKET_HOST = '127.0.0.1'  # Установка SOCKET_HOST для хоста сокет-сервера
SOCKET_PORT = 5000  # Установка SOCKET_PORT для порта сокет-сервера
DATA_JSON = 'storage/data.json'
JSON_FILE = Path("storage/data.json")


if not JSON_FILE.is_file():
    data = {}
    with open(JSON_FILE, "w") as file:
        json.dump(data, file)

class GoitFramework(BaseHTTPRequestHandler):

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)  # Разбор пути запроса

        if route.path == '/':
            self.send_html('index.html')
        elif route.path == '/message':
            self.send_html('message.html')
        else:
            file = BASE_DIR.joinpath(route.path[1:])
            if file.exists():
                self.send_static(file)
            else:
                self.send_html('error.html', 404)

    def do_POST(self):
        size = self.headers.get('Content-Length')  # Получение длины содержимого запроса
        data = self.rfile.read(int(size))  # Чтение данных запроса

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Создание UDP-сокета
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))  # Отправка данных на сокет-сервер
        client_socket.close()  # Закрытие сокета

        self.send_response(302)  # Отправка статусного кода 302 (перенаправление)
        self.send_header('Location', '/message')  # Установка заголовка Location для перенаправления
        self.end_headers()  # Завершение заголовков HTTP

    def send_html(self, filename, status_code=200):
    # Отправка HTML-контента в качестве ответа

        self.send_response(status_code)  # Отправка статусного кода
        self.send_header('Content-Type', 'text/html')  # Установка заголовка Content-Type
        self.end_headers()  # Завершение заголовков HTTP

        with open(filename, 'r', encoding='utf-8') as file:  # Відкриття файлу в текстовому режимі з вказанням кодування
            self.wfile.write(file.read().encode('utf-8'))  # Запис содержимого файла в відповідь після закодування у байти

    def send_static(self, filename, status_code=200):
    # Отправка статических файлов в качестве ответа

        self.send_response(status_code)  # Отправка статусного кода
        mime_type, *_ = mimetypes.guess_type(filename)  # Определение MIME-типа файла
        if mime_type:  # Если MIME-тип определен
            self.send_header('Content-Type', mime_type)  # Установка заголовка Content-Type
        else:
            self.send_header('Content-Type', 'text/plain')  # Установка заголовка Content-Type по умолчанию
        self.end_headers()  # Завершение

        with open(filename, 'rb') as file:  # Відкриття файлу в бінарному режимі
            self.wfile.write(file.read())  # Запис содержимого файла в відповідь

def save_data_from_form(data):
    parse_data = urllib.parse.unquote_plus(data.decode())  # Декодирование и разбор данных формы
    try:
        parse_dict = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        parse_dict['timestamp'] = timestamp
        with open(DATA_JSON, 'r+') as file:
            json_data = json.load(file)
            json_data[timestamp] = parse_dict
            file.seek(0)
            json.dump(json_data, file, ensure_ascii=False, indent=4)
            file.truncate()
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)

def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Создание UDP-сокета
    server_socket.bind((host, port))  # Привязка сокета к хосту и порту
    logging.info("Starting socket server")  # Логирование запуска сервера
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)  # Получение данных от клиента
            logging.info(f"Socket received {address}: {msg}")  # Логирование полученных данных
            save_data_from_form(msg)  # Сохранение данных из формы
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()

def run_http_server(host, port):
    address = (host, port)  # Установка адреса сервера
    http_server = HTTPServer(address, GoitFramework)  # Создание HTTP-сервера
    logging.info("Starting http server")  # Логирование запуска сервера
    try:
        http_server.serve_forever()  # Запуск бесконечного цикла обработки запросов
    except KeyboardInterrupt:
        pass
    finally:
        http_server.server_close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')  # Настройка логирования
    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))  # Создание потока для HTTP-сервера
    server.start()  # Запуск потока
    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))  # Создание потока для сокет-сервера
    server_socket.start()  # Запуск потока