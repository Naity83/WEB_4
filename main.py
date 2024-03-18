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

class GoitFramework(BaseHTTPRequestHandler):
    
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)  # Разбор пути запроса
        
        match route.path:
            case '/':  # Обработка корневого пути
                self.send_html('index.html')  # Отправка файла index.html
            case '/message':  # Обработка пути message
                self.send_html('message.html')  # Отправка файла message.html
            case '/contact':  # Обработка пути contact
                self.send_html('contact.html')  # Отправка файла contact.html
            case _:  # Обработка остальных путей
                file = BASE_DIR.joinpath(route.path[1:])  # Получение пути к файлу
                if file.exists():  # Проверка существования файла
                    self.send_static(file)  # Отправка статического файла
                else:
                    self.send_html('error.html', 404)  # Отправка страницы 404 HTML, если файл не существует

    def do_POST(self):
        size = self.headers.get('Content-Length')  # Получение длины содержимого запроса
        data = self.rfile.read(int(size))  # Чтение данных запроса

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Создание UDP-сокета
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))  # Отправка данных на сокет-сервер
        client_socket.close()  # Закрытие сокета

        self.send_response(302)  # Отправка статусного кода 302 (перенаправление)
        self.send_header('Location', '/contact')  # Установка заголовка Location для перенаправления
        self.end_headers()  # Завершение заголовков HTTP

    def send_html(self, filename, status_code=200):
        # Отправка HTML-контента в качестве ответа
        self.send_response(status_code)  # Отправка статусного кода
        self.send_header('Content-Type', 'text/html')  # Установка заголовка Content-Type
        self.end_headers()  # Завершение заголовков HTTP
        with open(filename, 'rb') as file:  # Открытие файла в бинарном режиме
            self.wfile.write(file.read())  # Запись содержимого файла в ответ

    def render_template(self, filename, status_code=200):
        # Рендеринг шаблона Jinja2
        self.send_response(status_code)  # Отправка статусного кода
        self.send_header('Content-Type', 'text/html')  # Установка заголовка Content-Type
        self.end_headers()  # Завершение заголовков HTTP
        with open('storage/db.json', 'r', encoding='utf-8') as file:  # Открытие JSON-файла для чтения
            data = json.load(file)  # Загрузка данных JSON из файла
        message = None  # Установка сообщения по умолчанию
        html = template.render(blogs=data, message=message)  # Рендеринг шаблона с данными
        self.wfile.write(html.encode())  # Запись сгенерированного HTML в ответ

    def send_static(self, filename, status_code=200):
        # Отправка статических файлов в качестве ответа
        self.send_response(status_code)  # Отправка статусного кода
        mime_type, *_ = mimetypes.guess_type(filename)  # Определение MIME-типа файла
        if mime_type:  # Если MIME-тип определен
            self.send_header('Content-Type', mime_type)  # Установка заголовка Content-Type
        else:
            self.send_header('Content-Type', 'text/plain')  # Установка заголовка Content-Type по умолчанию
        self.end_headers()  # Завершение заголовков HTTP
        with open(filename, 'rb') as file:  # Открытие файла в бинарном режиме
            self.wfile.write(file.read())  # Запись содержимого файла в ответ

def save_data_from_form(data):
    # Функция для сохранения данных формы в JSON-файле
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
    # Функция для запуска сокет-сервера
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Создание UDP-сокета
    server_socket.bind((host, port))  # Привязка сокета к хосту и порту
    logging.info("Starting socket server")  # Логирование запуска сервера
    try:
        while True:  # Запуск цикла сервера
            msg, address = server_socket.recvfrom(BUFFER_SIZE)  # Получение данных от клиента
            logging.info(f"Socket received {address}: {msg}")  # Логирование полученных данных
            save_data_from_form(msg)  # Сохранение данных из формы
    except KeyboardInterrupt:  # Обработка прерывания с клавиатуры
        pass
    finally:
        server_socket.close()  # Закрытие сокета

def run_http_server(host, port):
    # Функция для запуска HTTP-сервера
    address = (host, port)  # Установка адреса сервера
    http_server = HTTPServer(address, GoitFramework)  # Создание HTTP-сервера
    logging.info("Starting http server")  # Логирование запуска сервера
    try:
        http_server.serve_forever()  # Запуск бесконечного цикла обработки запросов
    except KeyboardInterrupt:  # Обработка прерывания с клавиатуры
        pass
    finally:
        http_server.server_close()  # Закрытие сервера

if __name__ == '__main__':
    # Главная точка входа в программу
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')  # Настройка логирования
    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))  # Создание потока для HTTP-сервера
    server.start()  # Запуск потока
    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))  # Создание потока для сокет-сервера
    server_socket.start()  # Запуск потока