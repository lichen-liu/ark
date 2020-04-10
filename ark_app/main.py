from flask import render_template
from ark_app import account, webapp


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

    def __init__(self, error_message=None, title='Welcome!', url_screenshot_info=None):
        self.error_message = error_message
        self.title = title
        self.url_screenshot_info = url_screenshot_info


def main(guest_welcome_args=GuestWelcomeArgs(), user_welcome_args=UserWelcomeArgs()):
    if account.account_is_logged_in():
        return main_user_welcome(user_welcome_args)
    else:
        return main_guest_welcome(guest_welcome_args)


def main_guest_welcome(args):
    return render_template('guest_welcome.html', title=args.title, username=args.username, password=args.password, error_message=args.error_message)


def main_user_welcome(args):
    return render_template('user_welcome.html', title=args.title, username=account.account_get_logged_in_username(), error_message=args.error_message, url_screenshot_info=args.url_screenshot_info)
