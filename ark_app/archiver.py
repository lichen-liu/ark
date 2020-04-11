from ark_app import webapp, webpage_snapshot, dynamodb, s3, main, account, url_util, searcher, archive_lambda
from flask import request, redirect
from bs4 import BeautifulSoup
import datetime
import archiveis
import re


RUNNING_LOCALLY = True


@webapp.route('/api/archive_url', methods=['GET', 'POST'])
def archive_url_handler():
    print('archive_url_handler')

    if not account.account_is_logged_in():
        return redirect('/')

    if request.method == 'POST':
        original_url = request.form.get('url_text')
    elif request.method == 'GET':
        original_url = request.args.get('url_text')

    if not url_util.precheck_url(original_url):
        return main.main(user_welcome_args=main.UserWelcomeArgs(error_message='Invalid URL: ' + (original_url if original_url else '')))

    dynamodb.push_account_archive_request(list_name=dynamodb.ACCOUNT_TABLE_ARCHIVE_PENDING_REQUEST_LIST,
                                          username=account.account_get_logged_in_username(), original_url=original_url)
    
    error_response, success_response = archive_lambda.archive_url(original_url=original_url, username=account.account_get_logged_in_username())
    # XOR check, only one response can be valid
    assert (error_response is None) != (success_response is None)

    if RUNNING_LOCALLY:
        return error_response if error_response else success_response
    else:
        return error_response if error_response else redirect('/')
