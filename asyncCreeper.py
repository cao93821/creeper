# import time
# import sys
#
#
# def draw():
#     while True:
#         for icon in ['/  ', '|  ', '\\  ', '——  ']:
#             sys.stdout.write('\r')
#             sys.stdout.write(icon)
#             sys.stdout.flush()
#             x = yield
#
#
# def time_waste():
#     current_time = 0
#     while True:
#         time.sleep(0.2)
#         current_time += 0.2
#         x = yield current_time
#
#
# def main():
#     total_time = 10
#     draw_machine = draw()
#     time_waste_machine = time_waste()
#     next(draw_machine)
#     next(time_waste_machine)
#     is_finished = False
#     while not is_finished:
#         draw_machine.send(1)
#         current_time = time_waste_machine.send(1)
#         if current_time >= total_time:
#             is_finished = True
#
#
# if __name__ == '__main__':
#     main()

import requests
import sys


def download(url, ):
    response = requests.get(url, stream=True)
    size = int(response.headers['content-length'])
    now_size = 0
    with open('test.mp4', 'wb') as f:
        for data in response.iter_content(chunk_size=1024):
            f.write(data)
            now_size += len(data)
            x = yield float(now_size/size)


def draw():
    while True:
        percentage = yield
        sys.stdout.write('\r')
        sys.stdout.write('正在下载 ' + '#' * int(20 * percentage))
        sys.stdout.flush()


def main():
    url = 'http://vod1oowvkrz.nosdn.127.net/574931449-192281719157761.mp4'
    download_machine = download(url)
    draw_machine = draw()
    next(download_machine)
    next(draw_machine)
    while True:
        try:
            percentage = download_machine.send(1)
        except StopIteration:
            sys.stdout.write('\r下载成功')
            break
        else:
            draw_machine.send(percentage)


if __name__ == '__main__':
    main()
















