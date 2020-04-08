import os

from ark_app import webapp, main, dynamodb


def init():
    '''
    All initialization should be done here
    '''
    
    print('INITIALIZE')

    # Create arkAccount Table if necessary
    dynamodb.create_account_table()