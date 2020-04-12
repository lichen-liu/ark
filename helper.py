#!venv/bin/python

import boto3
import shutil
import os
import argparse
import time
from corelib import dynamodb, utility, s3, static_resources
from zipfile import ZipFile


def wait_for_countdown(seconds):
    countdown = seconds
    while countdown > 0:
        print('Waiting for', countdown, 'seconds', '...')
        time.sleep(1)
        countdown -= 1
    print('    Done')


def clear_archive():
    print('Clearing', dynamodb.ARCHIVE_TABLE, '...')
    dynamodb.clear_archive_table()
    print('    Succeeded')

    print('Deleting', s3.get_s3_path_in_string(key='', bucket_name=s3.BUCKET), '...')
    s3.delete_directory_content(directory='', bucket_name=s3.BUCKET)
    print('    Succeeded')

    print('\n')


def clear_all():
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


ARK_ARCHIVER_LAMBDA = 'ark-archiver-lambda'
ARK_ARCHIVER_LAMBDA_S3_BUCKET = 'clr-ark-archiver-lambda'

def update_lambda():
    build_path = 'build'
    build_src_path = os.path.join(build_path, 'src')
    
    build_base_zip_file = 'build_base.zip'
    build_zip_file = 'build.zip'
    archivelib_dir = 'archivelib'
    corelib_dir = 'corelib'
    lambda_function_file = 'lambda_function_archiver.py'
    cache_dir = '__pycache__'

    dst_archivelib_path = os.path.join(build_src_path, archivelib_dir)
    dst_corelib_path = os.path.join(build_src_path, corelib_dir)
    dst_archivelib_cache_path = os.path.join(os.path.join(build_src_path, archivelib_dir), cache_dir)
    dst_corelib_cache_path = os.path.join(os.path.join(build_src_path, corelib_dir), cache_dir)

    print('Updateing Lambda Function Code for', ARK_ARCHIVER_LAMBDA, '...')

    if not os.path.exists(build_base_zip_file):
        print('Error: No', build_base_zip_file, 'file found!')
        return

    print('Creating temporary dir', build_path)
    if os.path.exists(build_path):
        shutil.rmtree(build_path)
    os.makedirs(build_path)

    print('Deleting', build_zip_file)
    if os.path.exists(build_zip_file):
        os.remove(build_zip_file)

    print('Extracting all files in ' + build_base_zip_file + ' to ' + build_path)
    with ZipFile(build_base_zip_file, 'r') as zipObj:
        zipObj.extractall(build_path)

    print('Deleting all files in ' + build_src_path)
    if os.path.exists(build_src_path):
        shutil.rmtree(build_src_path)
    os.makedirs(build_src_path)

    print('Copying ' + archivelib_dir + ' to ' + build_src_path)
    shutil.copytree(archivelib_dir, dst_archivelib_path)
    print('Copying ' + corelib_dir + ' to ' + build_src_path)
    shutil.copytree(corelib_dir, dst_corelib_path)
    print('Copying ' + lambda_function_file + ' to ' + build_src_path)
    shutil.copy2(lambda_function_file, os.path.join(build_src_path, lambda_function_file))

    print('Deleting', dst_archivelib_cache_path)
    if os.path.exists(dst_archivelib_cache_path):
        shutil.rmtree(dst_archivelib_cache_path)

    print('Deleting', dst_corelib_cache_path)
    if os.path.exists(dst_corelib_cache_path):
        shutil.rmtree(dst_corelib_cache_path)

    print('Zipping all files in', build_path, 'to', build_zip_file)
    shutil.make_archive(build_path, 'zip', build_path)
    
    print('Deleting temporary dir', build_path)
    shutil.rmtree(build_path)

    if s3.create_bucket_if_necessary(bucket_name=ARK_ARCHIVER_LAMBDA_S3_BUCKET):
        print('Created S3 Bucket', ARK_ARCHIVER_LAMBDA_S3_BUCKET)
    
    print('Uploading', build_zip_file, 'to S3', ARK_ARCHIVER_LAMBDA_S3_BUCKET)
    s3.upload_file(key=build_zip_file, filename=build_zip_file, bucket_name=ARK_ARCHIVER_LAMBDA_S3_BUCKET, public=True)

    print('Updating Lambda Function Code for', ARK_ARCHIVER_LAMBDA)
    boto3.client('lambda').update_function_code(
        FunctionName=ARK_ARCHIVER_LAMBDA,
        S3Bucket=ARK_ARCHIVER_LAMBDA_S3_BUCKET,
        S3Key=build_zip_file)

    print('Deleting', build_zip_file)
    if os.path.exists(build_zip_file):
        os.remove(build_zip_file)

    print('    Succeeded')
    print('\n')


def reset():
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



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--clear_archive', help='Clear all Archive Data (DynamoDB + S3)', action='store_true')
    parser.add_argument('--clear_all', help='Clear all Account and Archive Data (DynamoDB + S3)', action='store_true')
   
    parser.add_argument('--update_resources', help='Update all static resources to S3', action='store_true')
    parser.add_argument('--update_lambda', help='Update Lambda Function(' + ARK_ARCHIVER_LAMBDA + ')', action='store_true')
    parser.add_argument('--update_zappa', help='Update Flask with Zappa', action='store_true')

    parser.add_argument('--account_table', help='Print ' + dynamodb.ACCOUNT_TABLE + ' from DynamoDB‎', action='store_true')
    parser.add_argument('--archive_table', help='Print ' + dynamodb.ARCHIVE_TABLE + ' from DynamoDB', action='store_true')
    parser.add_argument('--s3', help='Print ' + s3.BUCKET + ' from S3', action ='store_true')

    parser.add_argument('--reset', help='Reset everything', action='store_true')
    parser.add_argument('--confirm', help='Confirm', action='store_true')

    args = parser.parse_args()


    if s3.create_bucket_if_necessary(bucket_name=s3.BUCKET):
        print('Created S3 Bucket', s3.BUCKET)
        print('\n')


    if args.clear_archive:
        clear_archive()


    if args.clear_all:
        clear_all()


    if args.update_resources:
        print('Updating Resources to ' + static_resources.S3_BUCKET, '...')
        static_resources.update_resources_to_s3()
        print('    Succeeded')
        print('\n')
    

    if args.update_lambda:
        update_lambda()

    
    if args.update_zappa:
        print("Forwarding 'zappa update dev'", '...')
        from zappa import cli
        zappa_cli = cli.ZappaCLI()
        zappa_cli.handle(argv=['update', 'dev'])
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
        reset()
