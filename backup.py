#!/usr/bin/env python
import requests
from BeautifulSoup import BeautifulSoup as bs
import os
import sys
import re
from wsgiref.handlers import format_date_time


ignored_sections = { 'instagram', 'shop', 'blog', 'info & contact', 'video', }



class Archive(object):
    def __init__(self, basedir):
        print 'Saving files to', basedir
        if not os.path.isdir(basedir):
            os.mkdir(basedir)

        self.basedir = basedir


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

        r.raise_for_status()

        if r.status_code != 200:
            print '%s error getting photo %s' % (r.status_code, href)
            sys.exit(-1)
            
        open(fullpath, 'w').write(r.content)
        print 'Saved', path


archive = Archive(os.path.realpath('archive'))



def crawl():
    soup = bs(requests.get('http://www.elizabethweinberg.com').content)
    sections = soup.findAll('li', {
        'class': re.compile('.*page_in_a_section.*')
    })
    
    for s in sections:
        link = s.find('a')

        if link.text.lower() in ignored_sections:
            continue
        
        crawl_section(link.text.strip(), link['href'])


def crawl_section(name, href):
    print 'Crawling section "%s"' % name
    soup = bs(requests.get(href).content)
    save_photos(name, soup)
    crawl_subsections(name, soup)


def crawl_subsections(name, soup):
    thumbs = soup.find('ul', { 'class': re.compile('.*thumbnails.*') })
    subsections = thumbs.findAll('a', {
        'href': re.compile('.*elizabethweinberg.com.*')
    })
    for ss in subsections:
        crawl_section(os.path.join(name, ss['title'].strip()), ss['href'])

        
def save_photos(name, soup):
    photos = soup.findAll('a', { 'data-type': 'photo' })
    for p in photos:
        url = p.find('img')['data-src'].replace('500x500', '1600x1600')
        photo_name = url.split('/')[-1].strip()
        archive.save_photo(os.path.join(name, photo_name), url)

    

if __name__ == '__main__':
    crawl()
