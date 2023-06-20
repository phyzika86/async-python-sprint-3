"""
Файл запускающий сервер для обмена сообщениями на хост порт HOST PORT
"""
import socket
import threading
import logging
from datetime import datetime, timedelta
from collections import deque
import os
import shutil
import pickle
from collections import defaultdict
from config import HOST, PORT


class Server:
    def __init__(self, host: str = HOST, port: int = PORT, max_length_history: int = 20, ban_time: int = 4):
        """Инициализируем входные параметры сервера"""
        self.host = host
        self.port = port
        self.clients = []
        self.nicknames = []
        self.dict_clients = {}
        self.type_socket = socket.AF_INET  # Определяем тип соккета. Используем интернет сокет
        self.protocol = socket.SOCK_STREAM  # Определяем протокол. Используем TCP (transaction control protocol)
        self.banusers = defaultdict(lambda: dict(time=datetime.now(), foul=0))
        self.ban_time = ban_time
        try:
            with open(f"history_chat.txt", 'rb') as f:
                data = pickle.load(f)
            if isinstance(data, deque):
                self.history = data
            else:
                self.history = deque()
        except FileNotFoundError:
            self.history = deque()
        self.max_length_history = max_length_history

    def broadcast(self, message: bytes, nickname: str):
        """Вспомогательная функция для трансляции сообщений всем клиентам, подключенным к серверу"""
        for client in self.clients:
            client.send(datetime.now().strftime("%Y-%m-%d %H:%M:%S ").encode('utf-8') + f'({nickname}-общий): '.encode(
                'utf-8') + message)

    def private_cast(self, client, msg: bytes, from_user: str):
        client.send(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S ").encode('utf-8') + f'({from_user}-лс): '.encode('utf-8') + msg)

    @staticmethod
    def get_to_user_name(message: str) -> tuple[str, str]:
        """Метод определяет юзера которому будет адресовано сообщение или бан"""
        k = 0
        for sb in message:

            if sb == ' ':
                k += 1
                break
            else:
                k += 1

        to_user = message[1:k].strip()
        return to_user, message[k:].strip()

    def _update_history(self, message, nickname):
        message_history = datetime.now().strftime("%Y-%m-%d %H:%M:%S ").encode(
            'utf-8') + f'{nickname}: '.encode('utf-8') + message
        if len(self.history) < self.max_length_history:
            self.history.append(message_history)
        else:
            self.history.append(message_history)
            self.history.popleft()

        shutil.rmtree("history_chat.txt", ignore_errors=True)
        with open("history_chat.txt", 'wb') as f:
            pickle.dump(self.history, f, protocol=pickle.HIGHEST_PROTOCOL)

    def handle(self, client: socket, nickname: str):
        while True:
            try:
                message = client.recv(1024)  # Получаем сообщение от клиента
                if self.banusers[nickname]['foul'] >= 3:
                    if datetime.now() - self.banusers[nickname]['time'] < timedelta(hours=self.ban_time):
                        time_endban = self.banusers[nickname]['time'] + timedelta(hours=self.ban_time)
                        time_endban = time_endban.strftime('%Y-%m-%d %H:%M:%S')
                        self.private_cast(client=client,
                                          msg=f'Вы забанены. Бан истечет в {time_endban}'.encode('utf-8'),
                                          from_user='server')
                        continue
                    else:
                        self.banusers[nickname]['foul'] = 0
                decode_message = message.decode('utf-8')

                if decode_message[0] == '#':
                    to_user, _ = self.get_to_user_name(decode_message)
                    self.banusers[to_user]['foul'] += 1
                    if self.banusers[to_user]['foul'] == 3:
                        self.banusers[to_user]['time'] = datetime.now()
                        self.private_cast(client=self.dict_clients.get(to_user),
                                          msg='Вы забанены на 4 часа'.encode('utf-8'), from_user='server')
                    else:
                        if self.banusers[to_user]['foul'] < 3:
                            self.broadcast(message=f'{to_user} получил предупреждение'.encode('utf-8'),
                                           nickname='server')
                        else:
                            self.private_cast(client=client,
                                              msg=f'{to_user} уже забанен'.encode('utf-8'), from_user='server')
                    continue

                if decode_message[0] == '@':
                    to_user, msg = self.get_to_user_name(decode_message)
                    self.private_cast(client=self.dict_clients.get(to_user),
                                      msg=msg.encode('utf-8'), from_user=nickname)
                elif decode_message[0] == '$':
                    file_name = decode_message.split('$')[1]
                    extension = decode_message.split('$')[2]
                    control_suma = int(decode_message.split('$')[3])
                    with open(f'{file_name}.{extension}', 'ab+') as f:
                        size_file = 0
                        while True:
                            msg = client.recv(1024)
                            size_file += len(msg)
                            try:
                                error_load_file = msg.decode('utf-8')
                            except UnicodeDecodeError:
                                error_load_file = ''
                                logging.info(f'Возможно прилетел не текстовый файл')

                            try:
                                if error_load_file == 'ERROR_PATH':
                                    break
                                if size_file == control_suma:
                                    self.private_cast(client=client, msg=f'Файл успешно сохранен'.encode('utf-8'),
                                                      from_user='server')
                                    f.write(msg)
                                    break
                                else:
                                    f.write(msg)
                            except Exception as e:
                                logging.info(f'Произошла ошибка {e}')
                                break
                    if error_load_file == 'ERROR_SIZE':
                        os.remove(file_name)
                else:
                    self._update_history(message=message, nickname=nickname)
                    logging.info('Трансляция сообщения всем клиентам')
                    self.broadcast(message=message, nickname=nickname)

            except Exception as e:
                """
                В случае возникновения ошибки удаляем клиента и закрываем соединение
                """
                logging.error(f'Пользователь {nickname} удален по причине {e}')
                index = self.clients.index(client)
                self.clients.remove(client)
                client.close()
                nickname = self.nicknames[index]
                self.broadcast(f'{nickname} покинул чат!'.encode('utf-8'),
                               nickname='server')  # Кодируем в байты наше сообщение
                self.nicknames.remove(nickname)
                break

    def receive(self):
        server = socket.socket(self.type_socket, self.protocol)
        server.bind((self.host, self.port))
        server.listen()
        logging.info(f"Сервер хост: {self.host} ожидает подключения на порту: {self.port}")
        while True:
            # Accept Connection
            client, address = server.accept()
            logging.info(f"Клиент с адресом {str(address)} подключен к серверу. Пожалуйста, представься.")

            # Request And Store Nickname
            client.send('NICK'.encode('utf-8'))
            nickname = client.recv(1024).decode('utf-8')
            self.nicknames.append(nickname)
            self.clients.append(client)
            self.dict_clients[nickname] = client
            # Print And Broadcast Nickname
            print(f"Клиент с адресом {str(address)} представился как {nickname}")
            self.broadcast(f"{nickname} подключился!".encode('utf-8'), nickname='server')
            client.send('Вы успешно подключены!\n'.encode('utf-8'))
            for mes in self.history:
                client.send(mes + b'\n')

            # Запускаем поток для клиента
            thread = threading.Thread(target=self.handle, args=(client, nickname))
            thread.start()

    def listen(self):
        """Запуск сервера, который слушает подключения клиентов"""

        self.receive()


def start_server():
    server = Server()
    server.listen()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S',
    )
    start_server()
