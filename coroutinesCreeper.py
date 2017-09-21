"""爬虫的协程实现"""

import socket
import logging
import re
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE

from creeper import get_picture_url_list, URL, get_html


logging.basicConfig(level=logging.DEBUG,
                    format='levelname: %(levelname)s output msg: %(message)s')


url_list = get_picture_url_list(get_html(URL))
selector = DefaultSelector()


class Future:
    def __init__(self):
        self.result = None
        self._callbacks = []

    def add_callback(self, func):
        self._callbacks.append(func)

    def set_result(self, result):
        self.result = result
        for callback in self._callbacks:
            callback(self)


class Crawler:
    def __init__(self, crawler_url, crawler_id):
        self.id = crawler_id
        self.url = crawler_url
        # 这里的host要从url当中提取，不过有一个问题，为什么不同二级域名代表不同的host呢？
        self.host = re.sub(r'http://', '', re.findall(r'http.+com', self.url)[0])
        self.response = b''

    def fetch(self):
        sock = socket.socket()
        sock.setblocking(False)
        try:
            sock.connect((self.host, 80))
        except BlockingIOError:
            pass
        f = Future()

        def on_writeable():
            f.set_result(None)
        selector.register(sock.fileno(), EVENT_WRITE, on_writeable)
        yield f
        logging.debug('执行任务{}的连接操作'.format(self.id))
        selector.unregister(sock.fileno())
        get = 'GET {} HTTP/1.0\r\nHost: {}\r\n\r\n'.format(re.sub(r'http.+com', '', self.url), self.host)
        sock.send(get.encode('ascii'))
        while True:
            f = Future()

            def on_readable():
                f.set_result(sock.recv(4096))
            selector.register(sock.fileno(), EVENT_READ, on_readable)
            chunk = yield f
            logging.debug('执行任务{}的写入操作'.format(self.id))
            selector.unregister(sock.fileno())
            if chunk:
                self.response += chunk
            else:
                url_list.remove(self.url)
                # 先使用ascii解码为str，然后通过正则找出响应头
                response_head = re.findall(r'HTTP.+?\r\n\r\n', self.response.decode('ascii', errors='ignore'), flags=re.DOTALL)[0]
                # 截取响应头之后的二进制数据，由于ascii是一个字节表示一个字符，所以能够直接根据序号来截取二进制字节流
                response_content = self.response[len(response_head):]
                with open('{}.jpg'.format(self.id), 'wb') as f:
                    f.write(response_content)
                break


class Task:
    """这里Task的作用是什么呢？首先是创建下一阶段的future，为下一阶段的future插入回调函数，并启动future"""
    def __init__(self, coroutines):
        self.coroutines = coroutines
        # 初始化一个future，去执行coroutines
        self.future = Future()
        self.step(self.future)

    def step(self, future):
        try:
            next_future = self.coroutines.send(future.result)
        except StopIteration:
            return
        else:
            next_future.add_callback(self.step)
            self.future = next_future


def loop():
    while url_list:
        events = selector.select()
        for event_key, event_mask in events:
            callback = event_key.data
            callback()


if __name__ == '__main__':
    for index, url in enumerate(url_list):
        Task(Crawler(url, index).fetch())
    loop()

