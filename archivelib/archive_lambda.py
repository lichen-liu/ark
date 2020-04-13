from corelib import dynamodb, s3, url_util
from archivelib import webpage_snapshot
from bs4 import BeautifulSoup
import datetime
import archiveis
import re


def archive_url(original_url, username, running_locally):
    '''
    Return error_message if failed; otherwise None.
    '''
    error_message = None
    
    print('adjust_url(' + original_url + ')')
    url = url_util.adjust_url(original_url)
    if url is not None:
        # Record the current datetime
        utc_datetime = datetime.datetime.utcnow()
        utc_datetime_str = str(utc_datetime)

        # Save it on archive website
        try:
            print('archiveis.capture(' + url + ')')
            initial_archive_md_url = archiveis.capture(url)
        except Exception as e:
            print('Unexpected exception: ' + str(e))
            initial_archive_md_url = None
        
        # Screenshot the url webpage
        print('take_url_webpage_snapshot(' + url + ')')
        url_webpage_png, _url_inner_html = webpage_snapshot.take_url_webpage_snapshot(url=url, running_locally=running_locally)

        # Pop from pending
        dynamodb.pop_account_archive_request_by(list_name=dynamodb.ACCOUNT_TABLE_ARCHIVE_PENDING_REQUEST_LIST,
            username=username, original_url=original_url)

        # Create new archive entry on DynamoDB
        dynamodb.create_new_archive(url=url, datetime=utc_datetime_str, username=username, archive_md_url=initial_archive_md_url)

        # Store the screenshot on S3
        archive_id, _, _ = dynamodb.get_archive_info(url=url, datetime=utc_datetime_str)
        url_webpage_png_s3_key = s3.WEBPAGE_SCREENSHOT_DIR + archive_id + '.png'
        s3.upload_file_bytes_object(key=url_webpage_png_s3_key, file_bytes=url_webpage_png)

        # Store the text of the webpage on S3
        # url_webpage_text = clean_text(extract_text(url_inner_html)).encode()
        # url_weboage_text_s3_key = s3.WEBPAGE_TEXT_DIR + archive_id + '.txt'
        #s3.upload_file_bytes_object(key=url_weboage_text_s3_key, file_bytes=url_webpage_text)

        # Early-exit for success
        return None
    else:
        error_message = 'Invalid URL: ' + original_url

    # All success must early-exit
    assert error_message

    # Pop from pending
    dynamodb.pop_account_archive_request_by(list_name=dynamodb.ACCOUNT_TABLE_ARCHIVE_PENDING_REQUEST_LIST,
        username=username, original_url=original_url)
    # Add into failed
    dynamodb.push_account_archive_request(list_name=dynamodb.ACCOUNT_TABLE_ARCHIVE_FAILED_REQUEST_LIST,
        username=username, original_url=original_url)

    return error_message


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
