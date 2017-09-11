"""分别用阻塞式同步、阻塞式多线程、阻塞式多进程、非阻塞式同步、
非阻塞式异步这几种方式实现爬取10次example.com的任务
"""


import socket
import time
from concurrent import futures
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE


def blocking_way():
    sock = socket.socket()
    sock.connect(('example.com', 80))
    request = 'GET / HTTP1.0\r\nHost: example.com\r\n\r\n'
    sock.send(request.encode('ascii'))
    response = b''
    chunk = sock.recv(4096)
    while chunk:
        response += chunk
        chunk = sock.recv(4096)
    return response


def non_blocking_way():
    sock = socket.socket()
    sock.setblocking(False)
    # 由于使用非阻塞调用连接的时候，系统底层也会抛出异常，为什么呢？？
    # 好像是因为阻塞调用的时候这些异常不会抛出
    try:
        sock.connect(('example.com', 80))
    except BlockingIOError:
        pass
    request = 'GET / HTTP/1.0\r\nHost: example.com\r\n\r\n'
    data = request.encode('ascii')
    while True:
        try:
            sock.send(data)
            break
        except OSError:
            pass
    response = b''
    while True:
        try:
            chunk = sock.recv(4096)
            while chunk:
                response += chunk
                chunk = sock.recv(4096)
            break
        except OSError:
            pass
    return response


def sync_way():
    res = []
    for i in range(10):
        # res.append(blocking_way())
        res.append(non_blocking_way())
    return len(res)


def process_way():
    workers = 10
    with futures.ProcessPoolExecutor(workers) as executor:
        res = list(executor.submit(blocking_way) for i in range(10))
    return len([fut.result() for fut in res])


def thread_way():
    workers = 10
    with futures.ThreadPoolExecutor(workers) as executor:
        res = list(executor.submit(blocking_way) for i in range(10))
    return len([fut.result() for fut in res])


COUNT = 0
selector = DefaultSelector()


def non_blocking_way2():
    """回调形式"""
    sock = socket.socket()
    sock.setblocking(False)

    def connect(key, mask):
        selector.unregister(key.fd)
        request = 'GET / HTTP1.0\r\nHost: example.com\r\n\r\n'
        sock.send(request.encode('ascii'))
        selector.register(key.fd, EVENT_READ, read_response)

    def read_response(key, mask):
        global COUNT
        response = b''
        chunk = sock.recv(4096)
        # 一次性读完就好了吧
        if chunk:
            response += chunk
        else:
            selector.unregister(key.fd)
            COUNT += 1

    try:
        sock.connect(('example.com', 80))
    except BlockingIOError:
        pass
    selector.register(sock.fileno(), EVENT_WRITE, connect)


if __name__ == '__main__':
    current = float(time.time())
    # sync_way()
    # process_way()
    # thread_way()
    for i in range(10):
        non_blocking_way2()
    while COUNT < 9:
        events = selector.select()
        for event_key, event_mask in events:
            callback = event_key.data
            callback(event_key, event_mask)
    print('{:.2f}'.format(float(time.time()) - current))
