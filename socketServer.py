"""使用socket实现的简易http服务器，用来测试socket的工作原理"""

import socket


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('127.0.0.1', 8000))
while 1:
    pass
sock.listen(5)
while 1:
    pass
