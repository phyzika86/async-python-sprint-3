"""
Приветствую и заранее спасибо за ревью. Тесты по аплоаду файлов не получилось написать,
т.к.не всегда идет предсказуемое поведение. Бывает, при дебаге, что сообщения склеиваются. Пока не разобрался,
почему так. Еще тесты следует запускать по отдельности, так как в совокупности
"""
import os
import unittest
from server import start_server
from multiprocessing import Process
import socket
from config import HOST, PORT
from datetime import datetime, timedelta


def get_without_datetime(string):
    return ' '.join(string.decode('utf-8').split(' ')[2:])


class TCPClientTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            os.remove("history_chat.pickle")
        except:
            pass
        cls.client = client
        p = Process(target=start_server)
        cls.process = p

    def test_connection(self):
        self.process.start()
        self.client.connect((HOST, PORT))
        msg = self.client.recv(1024)
        self.assertEqual(msg, b'NICK')
        nickname = 'admin'
        self.client.send(f'{nickname}'.encode('utf-8'))
        msg = self.client.recv(1024)
        self.assertEqual(f'(server-общий): {nickname} подключился!', get_without_datetime(msg))
        msg = self.client.recv(1024)
        self.assertEqual(f'Вы успешно подключены!\n', msg.decode('utf-8'))
        send_msg = 'Hello'
        self.client.send(f'{send_msg}'.encode('utf-8'))
        msg = self.client.recv(1024)
        self.assertEqual(f'({nickname}-общий): {send_msg}', get_without_datetime(msg))
        self.process.terminate()

    def test_private_msg(self):
        self.process.start()
        self.client.connect((HOST, PORT))
        msg = self.client.recv(1024)
        self.assertEqual(msg, b'NICK')
        nickname = 'admin'
        self.client.send(f'{nickname}'.encode('utf-8'))
        msg = self.client.recv(1024)
        self.assertEqual(f'(server-общий): {nickname} подключился!', get_without_datetime(msg))
        msg = self.client.recv(1024)
        self.assertEqual(f'Вы успешно подключены!\n', msg.decode('utf-8'))
        send_msg = 'Helloadmin'
        self.client.send(f'@admin {send_msg}'.encode('utf-8'))
        msg = self.client.recv(1024)
        self.assertEqual(f'({nickname}-лс): {send_msg}', get_without_datetime(msg))
        self.process.terminate()

    def test_bun_user(self):
        self.process.start()
        self.client.connect((HOST, PORT))
        msg = self.client.recv(1024)
        self.assertEqual(msg, b'NICK')
        nickname = 'admin'
        self.client.send(f'{nickname}'.encode('utf-8'))
        msg = self.client.recv(1024)
        self.assertEqual(f'(server-общий): {nickname} подключился!', get_without_datetime(msg))
        msg = self.client.recv(1024)
        self.assertEqual(f'Вы успешно подключены!\n', msg.decode('utf-8'))
        user_bun = 'admin'
        self.client.send(f'#{user_bun}'.encode('utf-8'))
        msg = self.client.recv(1024)
        self.assertEqual(f'(server-общий): {user_bun} получил предупреждение', get_without_datetime(msg))
        self.client.send(f'#{user_bun}'.encode('utf-8'))
        msg = self.client.recv(1024)
        self.assertEqual(f'(server-общий): {user_bun} получил предупреждение', get_without_datetime(msg))
        self.client.send(f'#{user_bun}'.encode('utf-8'))
        msg = self.client.recv(1024)
        self.assertEqual(f'(server-лс): Вы забанены на 4 часа', get_without_datetime(msg))
        send_msg = 'Hello'
        self.client.send(f'{send_msg}'.encode('utf-8'))
        msg = self.client.recv(1024)
        date, time = msg.decode('utf-8').split(' ')[0:2]
        date_end = datetime.strptime(f'{date} {time}', '%Y-%m-%d %H:%M:%S') + timedelta(hours=4)
        self.assertEqual(f'(server-лс): Вы забанены. Бан истечет в {date_end.strftime("%Y-%m-%d %H:%M:%S")}',
                         get_without_datetime(msg))
        self.process.terminate()


if __name__ == '__main__':
    unittest.main()
