from corelib import s3
from os import listdir
from os.path import isfile, join, isdir
import boto3

S3_BUCKET = 'clr-ark-resources'
S3_STATIC_DIR = 'static/'
S3_ICONS_DIR = S3_STATIC_DIR + 'icons/'


def get_local_static_icons_dir_path():
    return join(join('ark_app', 'static'), 'icons')


def get_local_static_icon_files():
    '''
    (static_icons_dir_path, [file])
    '''
    icons_dir_path = get_local_static_icons_dir_path()
    files = [f for f in listdir(icons_dir_path) if isfile(join(icons_dir_path, f))]
    return (icons_dir_path, files)


def update_resources_to_s3():
    s3.create_bucket_if_necessary(bucket_name=S3_BUCKET)
    s3.create_directory_if_necessary(directory=S3_STATIC_DIR, bucket_name=S3_BUCKET)
    s3.create_directory_if_necessary(directory=S3_ICONS_DIR, bucket_name=S3_BUCKET)

    static_icons_dir_path, files = get_local_static_icon_files()
    for file in files:
        with open(join(static_icons_dir_path, file), 'rb') as data:
            s3.upload_file_object(key=S3_ICONS_DIR + file, file=data, bucket_name=S3_BUCKET, public=True)


def get_s3_static_icons_dir_path():
    return '{}/{}/{}'.format(boto3.client('s3').meta.endpoint_url, S3_BUCKET, S3_ICONS_DIR)


def get_static_icons_dir_path(local=True):
    if local:
        return '{}/{}'.format('..', S3_ICONS_DIR)
    else:
        return '{}/{}/{}'.format(boto3.client('s3').meta.endpoint_url, S3_BUCKET, S3_ICONS_DIR)
