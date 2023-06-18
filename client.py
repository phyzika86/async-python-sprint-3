# import asyncio
# import aiohttp
import logging
import socket
import threading


class Client:
    def __init__(self, server_host: str = "127.0.0.1", server_port: int = 8000, nickname: str = ''):
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

    def write(self) -> None:
        while True:
            message = f'{input()}'
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
