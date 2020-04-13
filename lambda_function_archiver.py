from corelib import dynamodb
from archivelib import archiver
import json
import os
import subprocess
import shutil
import time


BIN_DIR = '/tmp/bin'
CURR_BIN_DIR = os.getcwd() + '/bin'


def _init_bin(executable_name):
    start = time.clock()
    if not os.path.exists(BIN_DIR):
        print('Creating bin folder')
        os.makedirs(BIN_DIR)
    print('Copying binaries for ' + executable_name + ' in ' + BIN_DIR)
    currfile = os.path.join(CURR_BIN_DIR, executable_name)
    newfile = os.path.join(BIN_DIR, executable_name)
    shutil.copy2(currfile, newfile)
    print('Giving new binaries permissions for lambda')
    os.chmod(newfile, 0o775)
    elapsed = time.clock() - start
    print(executable_name + ' ready in ' + str(elapsed) + 's.')


def lambda_handler(event, lambda_context):
    _init_bin('headless-chromium')
    _init_bin('chromedriver')

    print(event)

    result = dynamodb_event_filter(event)
    print(result)

    if len(result) == 0:
        print('Nothing to handle!')
    else:
        error_count = 0
        for account_id, original_url in result:
            error_message = archiver.archive_url(original_url=original_url, username=account_id, running_locally=False)
            if error_message:
                error_count += 1
        
        print('Handled ' + str(len(result)) + ' items, ' + str(error_count) + ' items failed!')


def dynamodb_event_filter(event):
    '''
    Return [(account_id, original_url)]
    '''
    result = list()

    records = event.get('Records')
    if records is None:
        return result

    for record in records:
        if not (record.get('eventName') == 'MODIFY' and record.get('eventSource') == 'aws:dynamodb'):
            continue

        db = record.get('dynamodb')
        if db is None:
            continue
        
        keys = db.get('Keys')
        if keys is None:
            continue
        
        account_id_pair = keys.get('accountId')
        if account_id_pair is None:
            continue
        
        account_id = account_id_pair.get('S')
        if account_id is None:
            continue
        
        new_image = db.get('NewImage')
        old_image = db.get('OldImage')

        if new_image is None or old_image is None:
            continue

        new_pending_set = set(new_image.get(dynamodb.ACCOUNT_TABLE_ARCHIVE_PENDING_REQUEST_LIST, {'SS':list()})['SS'])
        old_pending_set = set(old_image.get(dynamodb.ACCOUNT_TABLE_ARCHIVE_PENDING_REQUEST_LIST, {'SS':list()})['SS'])

        difference_set = new_pending_set.difference(old_pending_set)
        if len(difference_set) == 0:
            continue

        original_url = next(iter(difference_set))
        result.append((account_id, original_url))

    return result
