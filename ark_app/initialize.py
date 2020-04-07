import os

from ark_app import webapp, directory, main
from common_lib import utility, s3, database


def init():
    '''
    All initialization should be done here
    '''
    
    print('INITIALIZE')

    # Initialize directories
    directory.create_directories_if_necessary()

    # Initialize S3
    s3.create_bucket_if_necessary()
    s3.create_directories_if_necessary()

    # Initialize RDS MySQL
    database.create_schema_if_necessary()
