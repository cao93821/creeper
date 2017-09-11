"""对于深入理解Python异步编程（上）当中的协程解决方案的学习和解读，第一个版本
https://mp.weixin.qq.com/s/fxsQEUeZ2nEJq9CiDyrHZA
"""


import socket
import logging
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE


logging.basicConfig(level=logging.DEBUG,
                    format='levelname: %(levelname)s output msg: %(message)s')


selector = DefaultSelector()
# 剩余任务数
left_tasks = 10


class Future:
    def __init__(self):
        # 期物的result就是每一个阶段的任务结果，而非整个任务的结果
        self.result = None
        # 为什么需要用列表来存储呢，同一时间应该只会有一个callback吧
        # 不能这样去想，任务管理器对于你这个任务完成以后所注册的回调函数
        # 并不一定只会有一个，现在只是刚好有一个而已
        self._callbacks = []

    def add_done_callback(self, func):
        """用来给任务管理器注册完成后的回调函数，也就是通过外部回调set_result
        之后的回调函数
        """
        self._callbacks.append(func)

    def set_result(self, result):
        """从一个普遍性的角度来说，set_result本身是给外部的回调函数调用的
        因此对于一个期物来说，完成一个阶段的任务，就会创建下一个阶段的任务，
        期物当中的注册的回调函数是用来在set_result的时候自动调用的，而回调
        函数的注册时间点也是在创建下一阶段任务的时候

        :param result: 阻塞操作的结果值回调
        """
        self.result = result
        for func in self._callbacks:
            func(self)


class Crawler:
    def __init__(self, crawler_id):
        self.id = crawler_id
        self.response = b''

    def fetch(self):
        sock = socket.socket()
        # 使用非阻塞模式
        sock.setblocking(False)
        try:
            sock.connect(('example.com', 80))
        # 使用非阻塞模式会raise阻塞模式下被过滤的一些无关紧要的异常
        except BlockingIOError:
            pass
        f = Future()

        def on_connected():
            """连接成功的回调函数"""
            f.set_result(None)

        selector.register(sock.fileno(), EVENT_WRITE, on_connected)
        yield f
        logging.debug('执行任务{}的连接操作'.format(self.id))
        selector.unregister(sock.fileno())
        get = 'GET / HTTP/1.0\r\nHost: example.com\r\n\r\n'
        sock.send(get.encode('ascii'))

        global left_tasks
        while True:
            f = Future()

            def on_readable():
                """socket可读的回调函数，默认接收低水位为1"""
                f.set_result(sock.recv(4096))

            selector.register(sock.fileno(), EVENT_READ, on_readable)

            # 这里的chunk是调用协程的时候send进来的，为什么要send进来呢，因为结果是
            # 通过on_readable回调函数传给f，然后再通过f传进来
            # 这里虽然看似是chunk = yield f 一句，但是流程其实完全割裂开了，其实好像
            # 没有必要传进来啊，直接调用f就行了，我可以尝试在后面打一个logger，但是传
            # 进来的话有个好处，就是可以少些一行代码，毕竟总是要send来继续协程的
            chunk = yield f
            logging.debug('执行任务{}的写入操作'.format(self.id))
            selector.unregister(sock.fileno())
            if chunk:
                self.response += chunk
            else:
                left_tasks -= 1
                logging.debug('任务{}完成, 剩余任务数为{}'.format(self.id, left_tasks))
                break


class Task:
    def __init__(self, executor):
        self.executor = executor
        f = Future()
        # 初始化Future，不过好像没有什么作用
        f.set_result(None)
        self.step(f)

    def step(self, future):
        try:
            next_future = self.executor.send(future.result)
        except StopIteration:
            # 当协程内循环break的时候就会raise StopIteration，这时候由于任务
            # 已经结束，因此直接return，不需要为期物添加回调了，新建的期物本身也由于
            # 不存在外部回调set_result而就此封存
            return
        next_future.add_done_callback(self.step)


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
