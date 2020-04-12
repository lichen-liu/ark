from ark_app import webapp, main, account, config
from flask import request, redirect, url_for
import datetime
from corelib import dynamodb, url_util, s3, utility


if config.RUNNING_LOCALLY:
    from archivelib import archive_lambda


@webapp.route('/api/search_or_archive_url', methods=['POST', 'GET'])
def main_search_or_archive_url_handler():
    if request.method == 'POST':
        action = request.form.get('action')
    elif request.method == 'GET':
        action = request.args.get('action')
    
    if action == 'archive_url_submit':
        return archive_url_handler()
    elif action == 'search_url_submit':
        return search_archive_by_url_datetimes_handler()
    else:
        assert False


@webapp.route('/api/archive_url', methods=['GET', 'POST'])
def archive_url_handler():
    print('archive_url_handler')

    if not account.account_is_logged_in():
        return redirect(url_for('main_handler'))

    if request.method == 'POST':
        original_url = request.form.get('url_text')
    elif request.method == 'GET':
        original_url = request.args.get('url_text')

    if not url_util.precheck_url(original_url):
        return main.main(user_welcome_args=main.UserWelcomeArgs(error_message='Invalid URL: ' + (original_url if original_url else '')))

    dynamodb.push_account_archive_request(list_name=dynamodb.ACCOUNT_TABLE_ARCHIVE_PENDING_REQUEST_LIST,
                                          username=account.account_get_logged_in_username(), original_url=original_url)

    if config.RUNNING_LOCALLY:
        # Only for local
        error_message = archive_lambda.archive_url(
            original_url=original_url, username=account.account_get_logged_in_username(), running_locally=True)
        if error_message:
            return main.main(user_welcome_args=main.UserWelcomeArgs(error_message=error_message))
        else:
            result = search_archive_by_url_datetimes(original_url)
            assert result
            proper_url, datetime, date_strs = result
            return main.main(
                user_welcome_args=main.UserWelcomeArgs(
                    error_message=error_message,
                    url_archive_info=UrlArchiveInfo(
                        query_url=original_url, proper_url=proper_url, created_datetime=datetime), date_strs=date_strs))  
    else:
        return redirect(url_for('main_handler'))


@webapp.route('/api/retry_archive_request', methods=['POST'])
def retry_archive_request_handler():
    if not account.account_is_logged_in():
        return redirect(url_for('main_handler'))
    
    original_url = request.form.get('url_text')
    request_list_short_name = request.form.get('request_list_name')
    print('retry_archive_request_handler(' + str(request_list_short_name) + ', ' + original_url + ')')
    
    if request_list_short_name == 'pending':
        list_name = dynamodb.ACCOUNT_TABLE_ARCHIVE_PENDING_REQUEST_LIST
    elif request_list_short_name == 'failed':
        list_name = dynamodb.ACCOUNT_TABLE_ARCHIVE_FAILED_REQUEST_LIST

    # Regardless whether it actually exists in the list,
    # archive the url again
    dynamodb.pop_account_archive_request_by(
        list_name=list_name, username=account.account_get_logged_in_username(), original_url=original_url)

    return redirect(url_for('archive_url_handler', url_text=original_url))


class UrlArchiveInfo:
    def __init__(self, proper_url, created_datetime, query_url=None):
        self.query_url = query_url if query_url else proper_url

        self.proper_url = proper_url
        self.created_datetime = created_datetime
        self.created_date = str(utility.iso_datetime_str_2_datetime(self.created_datetime).date())

        archive_id, self.created_username, self.archive_md_url = dynamodb.get_archive_info(url=self.proper_url, datetime=self.created_datetime)
        url_webpage_png_s3_key = s3.WEBPAGE_SCREENSHOT_DIR + archive_id + '.png'
        self.screenshot_url = s3.get_object_url(key=url_webpage_png_s3_key)


@webapp.route('/api/search_archive_by_url_datetimes', methods=['POST'])
def search_archive_by_url_datetimes_handler():
    print('search_archive_by_url_datetimes_handler')

    if not account.account_is_logged_in():
        return redirect(url_for('main_handler'))

    if request.method == 'POST':
        original_url = request.form.get('url_text')
        selected_date = request.form.get('selected_date') 
        selected_datetime = request.form.get('selected_datetime')
    elif request.method == 'GET':
        original_url = request.args.get('url_text')
        selected_date = request.args.get('selected_date') 
        selected_datetime = request.args.get('selected_datetime')

    if not url_util.precheck_url(original_url):
        return main.main(user_welcome_args=main.UserWelcomeArgs(error_message='Invalid URL: ' + (original_url if original_url else '')))
    
    if selected_date is not None:
        selected_date = utility.iso_date_str_2_date(selected_date)
        result = search_archive_by_url_datetimes(original_url, by_date = selected_date)
        if result is None:
            return main.main(user_welcome_args=main.UserWelcomeArgs(
                error_message=original_url + ' is not archived on ' + selected_date,
                prefill_url_text=original_url))
        
        proper_url, latest_datetime_str, datetime_strs = result
        return main.main(user_welcome_args=main.UserWelcomeArgs(
            url_archive_info=UrlArchiveInfo(proper_url=proper_url, created_datetime=latest_datetime_str, query_url=original_url),
            datetime_strs = datetime_strs))
    elif selected_datetime is not None:
        result = search_archive_by_url_datetimes(original_url, by_datetime = selected_datetime)
        if result is None:
            return main.main(user_welcome_args=main.UserWelcomeArgs(
                error_message=original_url + ' is not archived on ' + selected_datetime,
                prefill_url_text=original_url))
        
        proper_url, latest_datetime_str, datetime_strs = result
        return main.main(user_welcome_args=main.UserWelcomeArgs(
            url_archive_info=UrlArchiveInfo(proper_url=proper_url, created_datetime=latest_datetime_str, query_url=original_url),
            datetime_strs = datetime_strs))
    else :
        result = search_archive_by_url_datetimes(original_url)
        if result is None:
            return main.main(user_welcome_args=main.UserWelcomeArgs(
                error_message=original_url + ' is not archived yet',
                prefill_url_text=original_url))
        
        proper_url, latest_datetime_str, date_strs = result
        return main.main(user_welcome_args=main.UserWelcomeArgs(
            url_archive_info=UrlArchiveInfo(proper_url=proper_url, created_datetime=latest_datetime_str, query_url=original_url),
            date_strs = date_strs))


@webapp.route('/api/search_archive_by_exact', methods=['GET'])
def search_archive_by_exact_handler():
    if not account.account_is_logged_in():
        return redirect(url_for('main_handler'))

    exact_proper_url = request.args.get('proper_url')
    exact_datetime = request.args.get('datetime')
    print('exact_proper_url', exact_proper_url, 'exact_datetime', exact_datetime)
    return main.main(user_welcome_args=main.UserWelcomeArgs(url_archive_info=UrlArchiveInfo(proper_url=exact_proper_url, created_datetime=exact_datetime)))


@webapp.route('/api/search_all_archives_by_current_user', methods=['GET'])
def search_all_archives_by_current_user_handler():
    if not account.account_is_logged_in():
        return redirect(url_for('main_handler'))

    return main.main(user_welcome_args=main.UserWelcomeArgs(show_all_user_archive_list=True))


def search_archive_by_url_datetimes(original_url, by_date=None, by_datetime=None):
    '''
    by_date = datetime.date()
    by_datetime = datetime.datetime()
    Return (proper_url, latest_datetime, [datetime/date_str]), where datetime matches with the argument partial constraints.
    Return None if there are no archives for the url.
    '''
    url = url_util.adjust_url(original_url)
    if by_date is None and by_datetime is None:
        # No constraint, return list of dates
        datetime_strs = dynamodb.search_archive_by_url(url)
        if datetime_strs is None or len(datetime_strs) == 0:
            return None
        lastest_datetime_str = datetime_strs[0]
        date_strs = list({str(utility.iso_datetime_str_2_datetime(datetime_str).date()) for datetime_str in datetime_strs})
        return (url, lastest_datetime_str, date_strs)
    elif by_date is not None and by_datetime is None:
        # Date as constraint, return list of datetimes
        datetime_strs = dynamodb.search_archive_by_url(url, by_date)
        if datetime_strs is None or len(datetime_strs) == 0:
            return None
        lastest_datetime_str = datetime_strs[0]
        archive_info = dynamodb.get_archive_info(url, lastest_datetime_str)
        return (url, lastest_datetime_str, datetime_strs)
    elif by_date is None and by_datetime is not None:
        # Datetime as constraint, return itself
        datetime_str = str(by_datetime)
        archive_info = dynamodb.get_archive_info(url, datetime_str)
        return (url, datetime_str, [datetime_str])
    else:
        assert False
