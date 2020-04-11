from flask import render_template, redirect
from ark_app import account, webapp, dynamodb, searcher


@webapp.route('/', methods=['GET', 'POST'])
@webapp.route('/index', methods=['GET', 'POST'])
@webapp.route('/main', methods=['GET', 'POST'])
# Display an HTML page with links
def main_handler():
    return main()


@webapp.route('/api/clear_failed_message', methods=['POST'])
def main_clear_failed_message_handler():
    if account.account_is_logged_in():
        dynamodb.clear_account_archive_request_by(
            list_name=dynamodb.ACCOUNT_TABLE_ARCHIVE_FAILED_REQUEST_LIST, username=account.account_get_logged_in_username())
    return redirect('/')


class GuestWelcomeArgs:
    def __init__(self, username=None, password=None, error_message=None, title='Welcome to Ark!'):
        self.username = username
        self.password = password
        self.error_message = error_message
        self.title = title


class StatsInfo:
    class SiteInfo:
        def __init__(self):
            self.estimated_num_archives = str(dynamodb.get_estimated_num_archives())
            self.estimated_num_users = str(dynamodb.get_estimated_num_users())
    
    class UserInfo:
        def __init__(self):
            archives = dynamodb.search_archive_by_username(username=account.account_get_logged_in_username())
            self.num_unique_archived_url = str(len(set(next(zip(*archives))))) if len(archives) > 0 else 0
            self.num_archives = str(len(archives))

    def __init__(self):
        self.site = self.SiteInfo()
        self.user = self.UserInfo()


class UserWelcomeArgs:
    def __init__(self, error_message=None, title='Welcome!', url_archive_info = None,show_all_user_archive_list=False, date_strs = [], datetime_strs = []):
        '''
        url_archive_info = searcher.UrlArchiveInfo
        '''

        self.error_message = error_message
        self.title = title
        self.username = account.account_get_logged_in_username()
        self.url_archive_info = url_archive_info
        self.date_strs = date_strs
        self.datetime_strs = datetime_strs
        
        self.stats_info = None
        if self.url_archive_info is None:
            # If url_archive_info is not available, show stats_info
            self.stats_info = StatsInfo()

        self.show_all_user_archive_list = show_all_user_archive_list
        if self.show_all_user_archive_list:
            self.user_archive_list = dynamodb.search_archive_by_username(username=self.username)
        else:
            self.user_archive_list = dynamodb.search_archive_by_username(username=self.username, num_latest_archive=20)

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
    user_archive_list_pair=(args.show_all_user_archive_list, args.user_archive_list),
    pending_list=args.pending_list, failed_list=args.failed_list, 
    dates_with_archives = args.date_strs,
    datetime_with_archives = args.datetime_strs)
