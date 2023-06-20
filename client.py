"""
Файл обработчик коннекта клиента к серверу и обмена сообщениями с другими клиентами сервера.
@login Hello - команда отправить пользователю login сообщение Hello
для загрузки файлов требуется использовать команду UPLOAD
#login - команда отправит жалобу на пользователя login
"""
import logging
import socket
import threading
import os
from datetime import datetime
from config import HOST, PORT

LIMIT_FILE_SIZE = 5


class Client:
    def __init__(self, server_host: str = HOST, server_port: int = PORT, nickname: str = ''):
        self.server_host = server_host
        self.server_port = server_port
        self.login = nickname
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def receive(self) -> None:
        while True:
            try:
                """Метод выводит все сообщения, которые пришли на сервер от других пользователей"""
                message = self.client.recv(1024).decode('utf-8')
                if message == 'NICK':
                    self.client.send(self.login.encode('utf-8'))
                else:
                    print(message)
            except Exception as e:
                """В сдучае ошибки отрубаем соединение"""
                logging.error(f"Произошла ошибка {e}")
                self.client.close()
                break

    def send_file(self) -> None:
        file_name = input('Укажите имя файла: ')
        extension = input('Укажите расширение файла: ')
        path = f'{file_name}.{extension}'
        file_name = file_name + datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
        if not os.path.exists(path):
            logging.error(f'Файла с названием {path} не существует')
            self.client.send(f'ERROR_PATH'.encode('utf-8'))
        else:
            stats = os.stat(path)
            if stats.st_size > LIMIT_FILE_SIZE * 1024 * 1024:
                logging.error(f'Загружаемый файл не может превышать {LIMIT_FILE_SIZE} Мбайт')
                self.client.send(f'ERROR_SIZE'.encode('utf-8'))
            with open(path, 'rb') as f:
                self.client.send(f'${file_name}${extension}${stats.st_size}'.encode('utf-8'))
                for line in f:
                    self.client.send(line)

    def write(self) -> None:
        while True:
            message = f'{input()}'
            if message == 'UPLOAD':
                self.send_file()
            else:
                self.client.send(message.encode('utf-8'))

    def connect_to_server(self) -> None:
        # Подключаемся к серверу
        self.client.connect((self.server_host, self.server_port))

        # Запускаем поток на получение данных от Сервера
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()

        # Запускаем поток на посылку данных на сервер
        write_thread = threading.Thread(target=self.write)
        write_thread.start()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S',
    )
    client = Client(nickname=input('Введите логин свой логин\n'))
    client.connect_to_server()
