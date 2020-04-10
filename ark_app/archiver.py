from ark_app import webapp, webpage_screenshoter, dynamodb, s3, main, account
from flask import request
import requests
import urllib.parse
import datetime


@webapp.route('/api/archive_url', methods=['POST'])
def archive_url_handler():
    url = adjust_url(request.form.get('archive_url_text'))
    if test_url(url):
        # Register the url and date to the database
        utc_date = str(datetime.datetime.utcnow().date())
        msg = dynamodb.create_new_archive(url=url, date=utc_date, username=account.account_get_logged_in_username())
        if msg:
            print(msg)
            return msg
    
        # Screenshot the url webpage
        url_webpage_png = webpage_screenshoter.take_url_webpage_screenshot_as_png(url)

        # Store the screenshot on S3
        archive_id, _ = dynamodb.get_archive_info(url=url, date=utc_date)
        url_webpage_png_s3_key = archive_id + '.png'
        s3.upload_file_bytes_object(key=url_webpage_png_s3_key, file_bytes=url_webpage_png)

        # TESTING
        # Print the screenshot
        screenshot_url = s3.get_object_url(key=url_webpage_png_s3_key)
        return main.main(user_welcome_args=main.UserWelcomeArgs(screenshot_url=screenshot_url))
    
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
