from ark_app import webapp, dynamodb, main, account, url_util, archive_lambda, searcher
from flask import request, redirect


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

    # Only for local
    error_message = archive_lambda.archive_url(original_url=original_url, username=account.account_get_logged_in_username())

    if RUNNING_LOCALLY:
        if error_message:
            return main.main(user_welcome_args=main.UserWelcomeArgs(error_message=error_message))
        else:
            result = searcher.search_archive_by_url_datetimes(original_url)
            assert result
            proper_url, datetime, date_strs = result
            return main.main(
                user_welcome_args=main.UserWelcomeArgs(
                    error_message=error_message,
                    url_archive_info=searcher.UrlArchiveInfo(
                        query_url=original_url, proper_url=proper_url, created_datetime=datetime), date_strs=date_strs))  
    else:
        return redirect('/')
