from datetime import timedelta


#############################
# DON'T TOUCH THIS CONSTANT #
#############################
# This value will be overwritten to False during
# helper.py --update_flask
RUNNING_LOCALLY = True


class Config(object):
    SECRET_KEY = 'NIDEMAMAMASHANGJIUYAOBAOZHALE'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes= 60 * 24)
    SESSION_REFRESH_EACH_REQUEST = True


################################
# AUTO-GENERATED SETTINGS HERE #
################################
