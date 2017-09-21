"""我自己的多线程爬虫，爬取10次计算时间"""

from concurrent.futures import ThreadPoolExecutor
import time

from creeper import get_html, get_picture_url_list, download_one, URL


MAX_WORKERS = 20


def download_all(url_list):
    workers = min(MAX_WORKERS, len(url_list))
    with ThreadPoolExecutor(workers) as executor:
        # 该语句会在所有线程为停止状态时结束，并且返回一个迭代器
        res = executor.map(download_one, url_list, range(len(url_list)))

    return len(list(res))


def main(url):
    html = get_html(url)
    picture_url_list = get_picture_url_list(html)
    t0 = time.time()
    download_all(picture_url_list)
    interval = time.time() - t0
    print('download all picture cost {:.2f} seconds'.format(interval))

if __name__ == '__main__':
    main(URL)