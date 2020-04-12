#!venv/bin/python

import shutil
import os
import argparse
import time
from corelib import dynamodb, utility, s3, static_resources


def wait_for_countdown(seconds):
    countdown = seconds
    while countdown > 0:
        print('Waiting for', countdown, 'seconds', '...')
        time.sleep(1)
        countdown -= 1
    print('    Done')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--update_resources', help='Update all static resources to S3', action='store_true')
    parser.add_argument('--clear_archive', help='Clear all Archive Data (DynamoDB + S3)', action='store_true')
    parser.add_argument('--clear_all', help='Clear all Account and Archive Data (DynamoDB + S3)', action='store_true')
    parser.add_argument('--account_table', help='Print ' + dynamodb.ACCOUNT_TABLE + ' from DynamoDB‎', action='store_true')
    parser.add_argument('--archive_table', help='Print ' + dynamodb.ARCHIVE_TABLE + ' from DynamoDB', action='store_true')
    parser.add_argument('--s3', help='Print ' + s3.BUCKET + ' from S3', action ='store_true')
    parser.add_argument('--reset', help='Reset everything', action='store_true')
    parser.add_argument('--confirm', help='Confirm', action='store_true')

    args = parser.parse_args()


    if args.update_resources:
        print('Updating Resources to ' + static_resources.S3_BUCKET, '...')
        static_resources.update_resources_to_s3()
        print('    Succeeded')
        print('\n')


    if s3.create_bucket_if_necessary(bucket_name=s3.BUCKET):
        print('Created S3 Bucket', s3.BUCKET)
        print('\n')


    if args.clear_archive:
        print('Clearing', dynamodb.ARCHIVE_TABLE, '...')
        dynamodb.clear_archive_table()
        print('    Succeeded')

        print('Deleting', s3.get_s3_path_in_string(key='', bucket_name=s3.BUCKET), '...')
        s3.delete_directory_content(directory='', bucket_name=s3.BUCKET)
        print('    Succeeded')

        print('\n')


    if args.clear_all:
        print('Clearing', dynamodb.ARCHIVE_TABLE, '...')
        dynamodb.clear_archive_table()
        print('    Succeeded')

        print('Clearing', dynamodb.ACCOUNT_TABLE, '...')
        dynamodb.clear_account_table()
        print('    Succeeded')

        print('Deleting', s3.get_s3_path_in_string(key='', bucket_name=s3.BUCKET), '...')
        s3.delete_directory_content(directory='', bucket_name=s3.BUCKET)
        print('    Succeeded')

        print('\n')


    if args.account_table:
        print(dynamodb.ACCOUNT_TABLE)
        table = dynamodb.get_table(dynamodb.ACCOUNT_TABLE)
        for row in table:
            print(row)
        print('\n')


    if args.archive_table:
        print(dynamodb.ARCHIVE_TABLE)
        table = dynamodb.get_table(dynamodb.ARCHIVE_TABLE)
        for row in table:
            print(row)
        print('\n')
    

    if args.s3:
        size, num_directory, num_file = s3.get_bucket_content_size(key='', bucket_name=s3.BUCKET)
        size_str = utility.convert_bytes_to_human_readable(size)
        print(s3.get_s3_path_in_string(key='', bucket_name=s3.BUCKET) + '  -----  ' + size_str + 
            ' (' + str(num_file) + ' files, ' + str(num_directory) + ' dirs)')
        print('\n')


    # Must be the last one to execute
    if args.reset and args.confirm:
        print('Warning: Resetting everything!')
        print('\n')

        print('Deleting', dynamodb.ARCHIVE_TABLE, '...')
        dynamodb.delete_table(dynamodb.ARCHIVE_TABLE)
        print('    Succeeded')

        print('Deleting', dynamodb.ACCOUNT_TABLE, '...')
        dynamodb.delete_table(dynamodb.ACCOUNT_TABLE)
        print('    Succeeded')

        print('Deleting', s3.get_s3_path_in_string(key='', bucket_name=s3.BUCKET), '...')
        s3.delete_directory_content(directory='', bucket_name=s3.BUCKET)
        print('    Succeeded')

        wait_for_countdown(10)

        print('Creating', dynamodb.ARCHIVE_TABLE, '...')
        dynamodb.create_archive_table()
        print('    Succeeded')

        print('Creating', dynamodb.ACCOUNT_TABLE, '...')
        dynamodb.create_account_table()
        print('    Succeeded')

        print('\n')
