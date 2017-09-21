""" creeper catch belle photos
在原有的基础上进行了重构，拆分成了多个函数
"""

import requests
import re


URL = "http://tieba.baidu.com/p/2166231880"


def get_html(url):
    response = requests.get(url)
    return response.content.decode('utf8')


def get_picture_url_list(html):
    matches = re.findall(r'<img pic_type="0" class="BDE_Image" src=".+?"', html)
    picture_url_list = [re.sub(r'<img pic_type="0" class="BDE_Image" src="', '', match).strip('"') for match in matches]
    return picture_url_list


def download_one(img_url, index):
    img = requests.get(img_url).content
    with open('test/{}.{}'.format(index, img_url[-img_url[::-1].find('.'):]), 'wb') as f:
        f.write(img)
        print(img)


def download_all(url_list):
    for index, picture_url in enumerate(url_list):
        download_one(picture_url, index)


def main(url):
    html = get_html(url)
    picture_url_list = get_picture_url_list(html)
    download_all(picture_url_list)

if __name__ == '__main__':
    main(URL)
