from ark_app import webapp, webpage_snapshot, dynamodb, s3, main, account
from flask import request
from bs4 import BeautifulSoup

import requests
import urllib.parse
import datetime
import archiveis
import re


@webapp.route('/api/archive_url', methods=['GET', 'POST'])
def archive_url_handler():
    if request.method == 'POST':
        original_url = request.form.get('archive_url_text')
    elif request.method == 'GET':
        original_url = request.args.get('archive_url_text')
    return archive_url(original_url)


def archive_url(original_url):
    error_message = None

    url = adjust_url(original_url)
    if url is not None:
        # Register the url and date to arkArchive
        utc_datetime = datetime.datetime.utcnow()
        utc_datetime_str = str(utc_datetime)
        utc_date_str = str(utc_datetime.date())
        username = account.account_get_logged_in_username()
        is_newly_created = dynamodb.create_new_archive(url=url, date=utc_date_str, username=username, datetime=utc_datetime_str)
        if not is_newly_created:
            previous_modified_username, previous_modified_datetime_str = dynamodb.update_archive_info_timestamp(
                url=url, date=utc_date_str, modified_username=username, modified_datetime=utc_datetime_str)

            error_message = 'Successfully rearchived. The archive was already created for url(' + url + \
                ') on (' + previous_modified_datetime_str + \
                ') by (' + previous_modified_username + ')!'

        # Screenshot the url webpage
        url_webpage_png, url_inner_html= webpage_snapshot.take_url_webpage_snapshot(url)

        # Save it on archive website
        archive_url = archiveis.capture(url)

        # Store the screenshot on S3
        archive_id, created_username, created_datetime, modified_username, modified_datetime = dynamodb.get_archive_info(url=url, date=utc_date_str)
        url_webpage_png_s3_key = s3.WEBPAGE_SCREENSHOT_DIR + archive_id + '.png'
        s3.upload_file_bytes_object(key=url_webpage_png_s3_key, file_bytes=url_webpage_png)

        # Store the text of the webpage on S3
        url_webpage_text = clean_text(extract_text(url_inner_html)).encode()
        url_weboage_text_s3_key = s3.WEBPAGE_TEXT_DIR + archive_id + '.txt'
        #s3.upload_file_bytes_object(key=url_weboage_text_s3_key, file_bytes=url_webpage_text)

        # TESTING
        # Print the screenshot
        screenshot_url = s3.get_object_url(key=url_webpage_png_s3_key)
        return main.main(
            user_welcome_args=main.UserWelcomeArgs(error_message=error_message, url_screenshot_info=main.UserWelcomeArgs.UrlArchiveInfo(archivemd_url=archive_url,
                                                                                                                                        screenshot_url=screenshot_url, query_url=original_url, adjusted_url=url,
                                                                                                                                        created_timestamp=created_datetime, modified_timestamp=modified_datetime, created_username=created_username, modified_username=modified_username
                                                                                                                                        )))
    else:
        error_message = 'Invalid URL: ' + original_url

    return main.main(user_welcome_args=main.UserWelcomeArgs(error_message=error_message))


def adjust_url(original_url):
    '''
    Return adjusted url if the url is reachable; otherwise None
    '''
    print('Original URL:', original_url)
    preprocessed_url = original_url.strip()
    preprocessed_url = preprocessed_url.lower()

    working_url = None
    for url_scheme in ['https', 'http']:
        url_parse = urllib.parse.urlparse(preprocessed_url, scheme=url_scheme)
        if url_parse.netloc == '':
            url_parse = url_parse._replace(netloc=url_parse.path)
            url_parse = url_parse._replace(path='')

        candidate_url = urllib.parse.urlunparse(url_parse)
        is_working = test_url(candidate_url)
        print('url_scheme='+url_scheme, 'candidate_url='+candidate_url,
              'candidate_url_components='+str(url_parse), 'is_working='+str(is_working))
        if is_working:
            working_url = candidate_url
            break

    return working_url


def test_url(url):
    '''
    Return True if url is reachable; otherwise False
    Try head request first; if failed, then try get request
    '''

    for request_func in [requests.head, requests.get]:
        try:
            r = request_func(url, timeout=5)
            if r.status_code == 200:
                return True
        except Exception:
            pass

    return False


def extract_text(raw_html):
    page = BeautifulSoup(raw_html, 'html.parser')
    page_titles = page.find_all('a1')
    page_paragraphs = page.find_all('p')
    page_contents = page_titles + page_paragraphs
    
    page_contents = [page_sentence.getText().strip() for page_sentence in page_contents]

    sentences = [sentence for sentence in page_contents if not '\n' in sentence]
    sentences = [sentence for sentence in sentences if '.' in sentence]

    return ' '.join(sentences)

def clean_text(text):
    return re.sub(r'[^\w!.]', ' ', text)