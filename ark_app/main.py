from flask import render_template
from ark_app import account, webapp, archiver, dynamodb, s3


@webapp.route('/', methods=['GET', 'POST'])
@webapp.route('/index', methods=['GET', 'POST'])
@webapp.route('/main', methods=['GET', 'POST'])
# Display an HTML page with links
def main_handler():
    return main()


class GuestWelcomeArgs:
    def __init__(self, username=None, password=None, error_message=None, title='Welcome to Image Gallery!'):
        self.username = username
        self.password = password
        self.error_message = error_message
        self.title = title


class UserWelcomeArgs:
    class UrlArchiveInfo:
        def __init__(self, proper_url, created_timestamp, query_url=None):
            self.query_url = query_url if query_url else proper_url

            self.proper_url = proper_url
            self.created_timestamp = created_timestamp

            archive_id, self.created_username, self.archive_md_url = dynamodb.get_archive_info(url=self.proper_url, datetime=self.created_timestamp)
            url_webpage_png_s3_key = s3.WEBPAGE_SCREENSHOT_DIR + archive_id + '.png'
            self.screenshot_url = s3.get_object_url(key=url_webpage_png_s3_key)


    def __init__(self, error_message=None, title='Welcome!', url_archive_info=None):
        self.error_message = error_message
        self.title = title
        self.username = account.account_get_logged_in_username()
        self.url_archive_info = url_archive_info
        self.success_list = dynamodb.search_archive_by_username(username=self.username, num_latest_archive=10)
        self.pending_list = dynamodb.get_account_archive_request_list(list_name=dynamodb.ACCOUNT_TABLE_ARCHIVE_PENDING_REQUEST_LIST, username=self.username)
        self.failed_list = dynamodb.get_account_archive_request_list(list_name=dynamodb.ACCOUNT_TABLE_ARCHIVE_FAILED_REQUEST_LIST, username=self.username)


def main(guest_welcome_args=None, user_welcome_args=None):
    if account.account_is_logged_in():
        if user_welcome_args is None:
            user_welcome_args = UserWelcomeArgs()
        return main_user_welcome(user_welcome_args)
    else:
        if guest_welcome_args is None:
            guest_welcome_args = GuestWelcomeArgs()
        return main_guest_welcome(guest_welcome_args)


def main_guest_welcome(args):
    return render_template('guest_welcome.html', title=args.title, username=args.username, password=args.password, error_message=args.error_message)


def main_user_welcome(args):
    return render_template('user_welcome.html', title=args.title, error_message=args.error_message,
    url_archive_info=args.url_archive_info,
    username=args.username,
    success_list=args.success_list, pending_list=args.pending_list, failed_list=args.failed_list, 
    timestamp_with_archives = ["2014","2015","2016","2017","2018","2019","2014","2015","2016","2017","2018","2019","2014","2015","2016","2017","2018","2019"], time_stamp_type = "year", dates_with_archives = ["2020-09-01","2020-09-02"])
