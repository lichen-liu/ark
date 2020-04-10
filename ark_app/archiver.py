from ark_app import webapp, webpage_screenshoter, dynamodb, s3, main, account
from flask import request
import requests
import urllib.parse
import datetime


@webapp.route('/api/archive_url', methods=['POST'])
def archive_url_handler():
    original_url = request.form.get('archive_url_text')
    url = adjust_url(original_url)
    error_message = None
    if test_url(url):
        # Register the url and date to the database
        utc_datetime = datetime.datetime.utcnow()
        utc_datetime_str = str(utc_datetime)
        utc_date_str = str(utc_datetime.date())
        is_newly_created = dynamodb.create_new_archive(url=url, date=utc_date_str, username=account.account_get_logged_in_username(), datetime=utc_datetime_str)
        if not is_newly_created:
            old_datetime_str = dynamodb.update_archive_info_timestamp(url=url, date=utc_date_str, new_datetime=utc_datetime_str)
            error_message = 'Successfully rearchived. The archive was already created for url(' + url + ') on (' + old_datetime_str + ')! '
        
        # Screenshot the url webpage
        url_webpage_png = webpage_screenshoter.take_url_webpage_screenshot_as_png(url)

        # Store the screenshot on S3
        archive_id, _, _ = dynamodb.get_archive_info(url=url, date=utc_date_str)
        url_webpage_png_s3_key = archive_id + '.png'
        s3.upload_file_bytes_object(key=url_webpage_png_s3_key, file_bytes=url_webpage_png)

        # TESTING
        # Print the screenshot
        screenshot_url = s3.get_object_url(key=url_webpage_png_s3_key)
        return main.main(user_welcome_args=main.UserWelcomeArgs(screenshot_url=screenshot_url, error_message=error_message))
    else:
        error_message = 'Invalid URL: ' + original_url
    
    return main.main(user_welcome_args=main.UserWelcomeArgs(error_message=error_message))


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
