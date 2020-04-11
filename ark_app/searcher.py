from ark_app import dynamodb, url_util, s3, main, account
import datetime
from flask import request, redirect
from ark_app import webapp


class UrlArchiveInfo:
    def __init__(self, proper_url, created_timestamp, query_url=None):
        self.query_url = query_url if query_url else proper_url

        self.proper_url = proper_url
        self.created_timestamp = created_timestamp

        archive_id, self.created_username, self.archive_md_url = dynamodb.get_archive_info(url=self.proper_url, datetime=self.created_timestamp)
        url_webpage_png_s3_key = s3.WEBPAGE_SCREENSHOT_DIR + archive_id + '.png'
        self.screenshot_url = s3.get_object_url(key=url_webpage_png_s3_key)


@webapp.route('/api/search_archive_by_url_datetimes', methods=['POST'])
def search_archive_by_url_datetimes_handler():
    if not account.account_is_logged_in():
        return redirect('/')

    url = request.form.get('url')
    calender_date = request.form.get('calender_date') #can rename it to 'exact_date'
    precise_date = request.form.get('precise_date') #can rename it to 'exact_datetime'
    
    if calender_date is not None :
        search_archive_by_url_datetimes(url, by_date = calender_date)
    elif precise_date is not None :
        search_archive_by_url_datetimes(url, by_datetime = precise_date)
    else :
        search_archive_by_url_datetimes(url)


@webapp.route('/api/search_archive_by_exact', methods=['GET'])
def search_archive_by_exact_handler():
    if not account.account_is_logged_in():
        return redirect('/')

    exact_proper_url = request.args.get('proper_url')
    exact_datetime = request.args.get('datetime')
    print('exact_proper_url', exact_proper_url, 'exact_datetime', exact_datetime)
    return main.main(user_welcome_args=main.UserWelcomeArgs(url_archive_info=UrlArchiveInfo(proper_url=exact_proper_url, created_timestamp=exact_datetime)))


@webapp.route('/api/search_all_archives_by_current_user', methods=['GET'])
def search_all_archives_by_current_user_handler():
    if not account.account_is_logged_in():
        return redirect('/')

    return main.main(user_welcome_args=main.UserWelcomeArgs(show_all_user_archive_list=True))


def search_archive_by_url_datetimes(original_url, by_date=None, by_datetime=None):
    '''
    by_date = datetime.date()
    by_datetime = datetime.datetime()
    Return (latest_datetime, get_archive_info(latest_datetime), [datetime/date_str]), where datetime matches with the argument partial constraints.
    Return None if there are no archives for the url.
    '''
    url = url_util.adjust_url(original_url)
    if by_date is None and by_datetime is None:
        # No constraint, return list of dates
        datetime_strs = dynamodb.search_archive_by_url(url)
        if datetime_strs is None or len(datetime_strs) == 0:
            return None
        lastest_datetime_str = datetime_strs[0]
        date_strs = list({str(datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S.%f').date()) for datetime_str in datetime_strs})
        archive_info = dynamodb.get_archive_info(url, lastest_datetime_str)
        return (lastest_datetime_str, archive_info, date_strs)
    elif by_date is not None and by_datetime is None:
        # Date as constraint, return list of datetimes
        datetime_strs = dynamodb.search_archive_by_url(url, by_date)
        if datetime_strs is None or len(datetime_strs) == 0:
            return None
        lastest_datetime_str = datetime_strs[0]
        archive_info = dynamodb.get_archive_info(url, lastest_datetime_str)
        return (lastest_datetime_str, archive_info, datetime_strs)
    elif by_date is None and by_datetime is not None:
        # Datetime as constraint, return itself
        datetime_str = str(by_datetime)
        archive_info = dynamodb.get_archive_info(url, datetime_str)
        return (datetime_str, archive_info, [datetime_str])
    else:
        assert False
