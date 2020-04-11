from ark_app import webapp, webpage_snapshot, dynamodb, s3, main, account, url_util
from flask import request
from bs4 import BeautifulSoup
import datetime
import archiveis
import re


@webapp.route('/api/archive_url', methods=['GET', 'POST'])
def archive_url_handler():
    if request.method == 'POST':
        original_url = request.form.get('archive_url_text')
    elif request.method == 'GET':
        original_url = request.args.get('archive_url_text')

    dynamodb.push_account_archive_request(list_name=dynamodb.ACCOUNT_TABLE_ARCHIVE_PENDING_REQUEST_LIST,
                                          username=account.account_get_logged_in_username(), original_url=original_url)
    assert dynamodb.pop_account_archive_request_by(
        list_name=dynamodb.ACCOUNT_TABLE_ARCHIVE_PENDING_REQUEST_LIST, username=account.account_get_logged_in_username(), original_url=original_url)
    return archive_url(original_url)


def archive_url(original_url):
    error_message = None

    url = url_util.adjust_url(original_url)
    if url is not None:
        # Register the url and date to arkArchive
        utc_datetime = datetime.datetime.utcnow()
        utc_datetime_str = str(utc_datetime)
        is_newly_created = dynamodb.create_new_archive(
            url=url, datetime=utc_datetime_str, username=account.account_get_logged_in_username())
        if is_newly_created:
            # Screenshot the url webpage
            url_webpage_png, url_inner_html = webpage_snapshot.take_url_webpage_snapshot(
                url)

            # Save it on archive website
            archivemd_url = archiveis.capture(url)

            # Store the screenshot on S3
            archive_id, username = dynamodb.get_archive_info(
                url=url, datetime=utc_datetime_str)
            url_webpage_png_s3_key = s3.WEBPAGE_SCREENSHOT_DIR + archive_id + '.png'
            s3.upload_file_bytes_object(
                key=url_webpage_png_s3_key, file_bytes=url_webpage_png)

            # Store the text of the webpage on S3
            # url_webpage_text = clean_text(extract_text(url_inner_html)).encode()
            # url_weboage_text_s3_key = s3.WEBPAGE_TEXT_DIR + archive_id + '.txt'
            #s3.upload_file_bytes_object(key=url_weboage_text_s3_key, file_bytes=url_webpage_text)

            # TESTING
            # Print the screenshot
            screenshot_url = s3.get_object_url(key=url_webpage_png_s3_key)
            return main.main(
                user_welcome_args=main.UserWelcomeArgs(error_message=error_message,
                                                       url_archive_info=main.UserWelcomeArgs.UrlArchiveInfo(archivemd_url=archivemd_url,
                                                                                                            screenshot_url=screenshot_url, query_url=original_url, adjusted_url=url,
                                                                                                            created_timestamp=utc_datetime_str, created_username=username
                                                                                                            )))
        else:
            error_message = 'Error: The archive was already created for url(' + \
                url + ') on (' + utc_datetime_str + ')!'
    else:
        dynamodb.push_account_archive_request(list_name=dynamodb.ACCOUNT_TABLE_ARCHIVE_FAILED_REQUEST_LIST,
                                              username=account.account_get_logged_in_username(), original_url=original_url)
        error_message = 'Invalid URL: ' + original_url

    return main.main(user_welcome_args=main.UserWelcomeArgs(error_message=error_message))


def extract_text(raw_html):
    page = BeautifulSoup(raw_html, 'html.parser')
    page_titles = page.find_all('a1')
    page_paragraphs = page.find_all('p')
    page_contents = page_titles + page_paragraphs

    page_contents = [page_sentence.getText().strip()
                     for page_sentence in page_contents]

    sentences = [
        sentence for sentence in page_contents if not '\n' in sentence]
    sentences = [sentence for sentence in sentences if '.' in sentence]

    return ' '.join(sentences)


def clean_text(text):
    return re.sub(r'[^\w!.]', ' ', text)


# THe following functions are dummy functions
def give_me_success_list(num=3):
    'Return a list of main.UserWelcomeArgs.UrlArchiveInfo'

    result = []
    for i in range(num):
        result.append(main.UserWelcomeArgs.UrlArchiveInfo(archivemd_url='success_{}.com'.format(str(i)),
                                                          screenshot_url='a', query_url='success_{}.com'.format(str(i)), adjusted_url='c',
                                                          created_timestamp=str(datetime.datetime.utcnow()), created_username=account.account_get_logged_in_username()
                                                          ))
    return result