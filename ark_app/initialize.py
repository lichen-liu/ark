from corelib import dynamodb, s3
from ark_app import config


def init():
    '''
    All initialization should be done here
    '''
    
    print('INITIALIZE')
    print('RUNNING_LOCALLY', config.RUNNING_LOCALLY)

    # Create arkAccount Table if necessary
    if dynamodb.create_account_table():
        print('Created DynamoDB Table', dynamodb.ACCOUNT_TABLE)
    if dynamodb.create_archive_table():
        print('Created DynamoDB Table', dynamodb.ARCHIVE_TABLE)

    # Create S3 directories if necessary
    if s3.create_bucket_if_necessary():
        print('Created S3 Bucket', s3.BUCKET)
    if s3.create_directory_if_necessary(directory=s3.WEBPAGE_SCREENSHOT_DIR):
        print('Created S3 Directory', s3.get_s3_path_in_string(s3.WEBPAGE_SCREENSHOT_DIR))
    if s3.create_directory_if_necessary(directory=s3.WEBPAGE_TEXT_DIR):
        print('Created S3 Directory', s3.get_s3_path_in_string(s3.WEBPAGE_TEXT_DIR))
