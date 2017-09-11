import time

from creeper import download_all, URL, get_picture_url_list, get_html


def main(url):
    html = get_html(url)
    picture_url_list = get_picture_url_list(html)
    t0 = time.time()
    download_all(picture_url_list)
    interval = time.time() - t0
    print('download all picture cost {:.2f} seconds'.format(interval))

if __name__ == '__main__':
    main(URL)







