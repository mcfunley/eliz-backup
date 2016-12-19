#!/usr/bin/env python
from bs4 import BeautifulSoup as bs
import requests
import os


def crawl():
    n = 0
    r = requests.get('http://www.elizabethweinberg.com/sitemap.xml')
    s = bs(r.content, 'xml')
    for url in s.findAll('url'):
        i = url.find('image')
        if not i:
            continue

        img_url = i.find('loc').string
        web_url = url.find('loc').string

        p = 'archive/%s' % web_url.split('/')[-2]
        if not os.path.isdir(p):
            os.makedirs(p)

        fullpath = '%s/%s.jpg' % (p, i.find('title').string)

        r = requests.get(img_url)
        open(fullpath, 'wb').write(r.content)
        print('Saved', fullpath)


if __name__ == '__main__':
    crawl()
