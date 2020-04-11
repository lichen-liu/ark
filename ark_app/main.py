from flask import render_template
from ark_app import account, webapp, dynamodb, searcher


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


# TODO: Retrieve all data
class StatsInfo:
    class SiteInfo:
        def __init__(self):
            self.num_unique_archived_url = str('N/A')
            self.num_archives = str('N/A')
            self.num_users = str('N/A')
            self.num_contributing_users = str('N/A')
    
    class UserInfo:
        def __init__(self):
            _username = account.account_get_logged_in_username()
            self.num_unique_archived_url = str('N/A')
            self.num_archives = str('N/A')

    def __init__(self):
        self.site = self.SiteInfo()
        self.user = self.UserInfo()


class UserWelcomeArgs:
    def __init__(self, error_message=None, title='Welcome!', url_archive_info=None):
        '''
        url_archive_info = searcher.UrlArchiveInfo
        '''

        self.error_message = error_message
        self.title = title
        self.username = account.account_get_logged_in_username()
        self.url_archive_info = url_archive_info
        
        self.stats_info = None
        if self.url_archive_info is None:
            # If url_archive_info is not available, show stats_info
            self.stats_info = StatsInfo()
        
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
    url_archive_info=args.url_archive_info, stats_info=args.stats_info,
    username=args.username,
    success_list=args.success_list, pending_list=args.pending_list, failed_list=args.failed_list,
    timestamp_with_archives = ["2014","2015","2016","2017","2018","2019","2014","2015","2016","2017","2018","2019","2014","2015","2016","2017","2018","2019"], time_stamp_type = "year", dates_with_archives = ["2020-09-01","2020-09-02"])
