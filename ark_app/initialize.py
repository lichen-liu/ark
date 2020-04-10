import os

from ark_app import webapp, main, dynamodb, s3


def init():
    '''
    All initialization should be done here
    '''
    
    print('INITIALIZE')

    # Create arkAccount Table if necessary
    dynamodb.create_account_table()

    # Create S3 directories if necessary
    s3.create_bucket_if_necessary()
    s3.create_directory_if_necessary(directory=s3.WEBPAGE_SCREENSHOT_DIR)