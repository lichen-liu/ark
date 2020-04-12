from datetime import timedelta


RUNNING_LOCALLY = False


class Config(object):
    SECRET_KEY = 'NIDEMAMAMASHANGJIUYAOBAOZHALE'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes= 60 * 24)
    SESSION_REFRESH_EACH_REQUEST = True


################################
# AUTO-GENERATED SETTINGS HERE #
################################
