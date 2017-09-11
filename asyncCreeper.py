

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
















