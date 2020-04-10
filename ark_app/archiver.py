from ark_app import webapp, webpage_screenshoter
from flask import request
import requests
import urllib.parse


@webapp.route('/api/archive_url', methods=['POST'])
def archive_url_handler():
    url = request.form.get('archive_url_text')
    url = adjust_url(url)
    if test_url(url):
        archive_url(url)
    
        print('yes')
        return 'yes'
    
    print('no')
    return 'no'


def adjust_url(url):
    print('Original URL:', url)
    url = url.strip()
    url = url.lower()
    url_parse = urllib.parse.urlparse(url, scheme='http')
    if url_parse.netloc == '':
        url_parse = url_parse._replace(netloc = url_parse.path)
        url_parse = url_parse._replace(path = '')
    print(url_parse)
    url = urllib.parse.urlunparse(url_parse)
    print('Adjusted URL:', url)
    return url



def test_url(url):
    '''
    Return True if url is reachable; otherwise False
    '''
    try:
        r = requests.head(url, timeout=2)
        if r.status_code == 200:
            return True
    except Exception:
        pass

    return False


def archive_url(url):
    print('archive_url(' + url + ')')
    url_webpage_png = webpage_screenshoter.take_url_webpage_screenshot_as_png(url)
