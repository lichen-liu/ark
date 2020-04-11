#from ark_app import dynamodb, url_util
import dynamodb, url_util
import datetime
from flask import request
from ark_app import webapp

@webapp.route('/api/search_url_by_date', methods=['POST'])
def search_url_by_date_handler():
    url = request.form.get('url')
    calender_date = request.form.get('calender_date')
    precise_date = request.form.get('precise_date')
    
    if calender_date is not None :
        search_url_archive_by_date(url, by_date = calender_date)
    elif precise_date is not None :
        search_url_archive_by_date(url, by_datetime = precise_date)
    else :
        search_url_archive_by_date(url)

def search_url_archive_by_date(original_url, by_date=None, by_datetime=None):
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

# print(search_url_archive_by_date(original_url='https://www.google.ca'))
# print('\n')
# print(search_url_archive_by_date(original_url='https://www.google.ca', by_date=datetime.date(2020, 4, 11)))
# print('\n')
# print(search_url_archive_by_date(original_url='https://www.google.ca', by_datetime=datetime.datetime(2020, 4, 11, 5, 30, 11, 754994)))
# print('\n')
