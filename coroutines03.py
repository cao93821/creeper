"""重构coroutines02"""

import socket
import logging
from selectors import EVENT_READ, EVENT_WRITE

from coroutines02 import Future, selector, Task


logging.basicConfig(level=logging.DEBUG,
                    format='levelname: %(levelname)s output msg: %(message)s')

left_tasks = 10


def connect(sock, address):
    f = Future()
    sock.setblocking(False)
    try:
        sock.connect(address)
    except BlockingIOError:
        pass

    def on_connected():
        f.set_result(None)

    selector.register(sock.fileno(), EVENT_WRITE, on_connected)
    yield f
    selector.unregister(sock.fileno())


def read(sock):
    f = Future()

    def on_readable():
        f.set_result(sock.recv(4096))

    selector.register(sock.fileno(), EVENT_READ, on_readable)
    chunk = yield f
    selector.unregister(sock.fileno())
    return chunk


def read_all(sock, id):
    """对于原流程只是一种改写，不过写两个yield from read(sock)有必要么，还不如之前那种呢
    response = []
    while True:
        chunk = yield from read(sock)
        logging.debug('执行任务{}的写入操作'.format(id))
        if chunk:
            response.append(chunk)
        else:
            break
    return b''.join(response)

    :param sock: socket连接
    :param id: 任务的id，要考虑下函数独立出来之后log怎么打，难道只能传id么？？
    :return: 响应结果(bytes)
    """
    response = []
    chunk = yield from read(sock)
    logging.debug('执行任务{}的写入操作'.format(id))
    while chunk:
        response.append(chunk)
        chunk = yield from read(sock)
        logging.debug('执行任务{}的写入操作'.format(id))
    return b''.join(response)


class Crawler:
    def __init__(self, crawler_id):
        self.id = crawler_id
        self.response = b''

    def fetch(self):
        global left_tasks
        sock = socket.socket()
        yield from connect(sock, ('example.com', 80))
        logging.debug('执行任务{}的连接操作'.format(self.id))
        get = 'GET / HTTP/1.0\r\nHost: example.com\r\n\r\n'
        sock.send(get.encode('ascii'))
        self.response = yield from read_all(sock, self.id)
        left_tasks -= 1


def loop():
    while left_tasks:
        # 获取所有处于完成事件
        # 根据api，select方法timeout参数为null时，会阻塞，直到一个file ready
        # 由于其原理不是pop那样，所以必须在处理过程当中unregister处理完的任务
        events = selector.select()
        # event_mask is a bitmask of events ready on this file object
        # 不清楚这个bitmask是什么
        for event_key, event_mask in events:
            callback = event_key.data
            callback()


if __name__ == '__main__':
    import time
    start = time.time()
    for i in range(left_tasks):
        crawler = Crawler(i + 1)
        Task(crawler.fetch())
    loop()
    print('{:.2f}'.format(time.time() - start))