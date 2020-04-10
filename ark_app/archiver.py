from ark_app import webapp, webpage_screenshoter
from flask import request


@webapp.route('/api/archive_url', methods=['POST'])
def archive_url_handler():
    url = request.form.get('archive_url_text')
    archive_url(url)
    return 'yes'


def archive_url(url):
    print(url)
    url_webpage_png = webpage_screenshoter.take_url_webpage_screenshot_as_png(url)
