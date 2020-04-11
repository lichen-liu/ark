from flask import render_template
from ark_app import account, webapp, archiver


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
        def __init__(self, archivemd_url=None, screenshot_url=None, query_url=None, adjusted_url=None, created_timestamp=None, created_username=None):
            self.screenshot_url = screenshot_url
            self.query_url = query_url
            self.adjusted_url = adjusted_url
            self.created_timestamp = created_timestamp
            self.created_username = created_username
            self.archivemd_url = archivemd_url

    def __init__(self, error_message=None, title='Welcome!', url_screenshot_info=None, success_list=None, pending_list=None, failed_list=None):
        self.error_message = error_message
        self.title = title
        self.url_screenshot_info = url_screenshot_info
        self.success_list = archiver.give_me_success_list(10)
        self.pending_list = archiver.give_me_pending_list(10)
        self.failed_list = archiver.give_me_failed_list(10)


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
    return render_template('user_welcome.html', title=args.title, username=account.account_get_logged_in_username(), error_message=args.error_message, url_screenshot_info=args.url_screenshot_info, success_list=args.success_list, pending_list=args.pending_list, failed_list=args.failed_list)
