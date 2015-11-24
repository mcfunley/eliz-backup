#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup
import os
import sys
import re
from wsgiref.handlers import format_date_time
import json


def bs(*args):
    args = list(args[:])
    args.append('html.parser')
    return BeautifulSoup(*args)


ignored_sections = { 'instagram', 'shop', 'blog', 'info & contact', 'video', }



class Archive(object):
    def __init__(self, basedir):
        print 'Saving files to', basedir
        if not os.path.isdir(basedir):
            os.mkdir(basedir)

        self.basedir = basedir
        self.broken_img_file = os.path.join(self.basedir, 'broken-images.txt')


    def save_photo(self, path, href):
        fullpath = os.path.join(self.basedir, path)
        d = os.path.dirname(fullpath)
        if not os.path.isdir(d):
            os.makedirs(d)

        headers = {}
        if os.path.isfile(fullpath):
            mtime = os.stat(fullpath).st_mtime
            headers['If-Modified-Since'] = format_date_time(mtime)

        r = requests.get(href, headers=headers)
        if r.status_code == 304:
            print 'File %s not modified.' % path
            return

        if r.status_code == 404:
            self.record_broken_image(href)
            return

        if r.status_code != 200:
            print >>sys.stderr, '%s error getting photo %s' % (r.status_code, href)
            sys.exit(1)
            
        open(fullpath, 'w').write(r.content)
        print 'Saved', path


    def reset_broken_images(self):
        open(self.broken_img_file, 'w').close()
        
    def record_broken_image(self, href):
        with open(self.broken_img_file, 'a') as f:
            print >>f, href
        print >>sys.stderr, '%s broken' % href


archive = Archive(os.path.realpath('archive'))
archive.reset_broken_images()

def href(element):
    h = element['href']
    if 'elizabethweinberg.com' in h:
        return h
    return 'http://elizabethweinberg.com/%s' % h.strip('/')


def generate_section_links():
    soup = bs(requests.get('http://www.elizabethweinberg.com').content)
    sections = soup.findAll('div', { 'class': 'thumbnail' })

    for s in sections:
        link = s.find('a')

        if link.text.lower() in ignored_sections:
            continue

        yield link.text.strip(), href(link)


def crawl():
    for name, href in generate_section_links():
        crawl_section(name, href)


def crawl_section(name, href):
    print 'Crawling section "%s" at %s' % (name, href)
    soup = bs(requests.get(href).content)
    save_photos(name, soup)
    crawl_subsections(name, soup)


def crawl_subsections(name, soup):
    thumbs = soup.find('ul', { 'class': re.compile('.*thumbnails.*') })
    if not thumbs:
        return
    
    subsections = thumbs.findAll('a', {
        'href': re.compile('.*elizabethweinberg.com.*')
    })
    for ss in subsections:
        crawl_section(os.path.join(name, ss['title'].strip()), ss['href'])


def generate_photo_urls(soup):
    project_detail = soup.find('script', { 'data-set': 'ProjectDetail' })
    data = json.loads(project_detail.text.strip())
    content_soup = bs(data['content'])
    for img in content_soup.findAll('img'):
        try:
            yield img['data-hi-res']
        except KeyError:
            yield img['src_o']

        
def save_photos(name, soup):
    for url in generate_photo_urls(soup):
        photo_name = url.split('/')[-1].strip()
        archive.save_photo(os.path.join(name, photo_name), url)

    

if __name__ == '__main__':
    crawl()
