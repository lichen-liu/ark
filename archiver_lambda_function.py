from corelib import dynamodb


def lambda_handler(event, lambda_context):
    print(event)
    result = dynamodb_event_filter(event)
    print(result)

    if len(result) == 0:
        return {
            'statusCode': 200,
            'body': json.dumps('Nothing to handle!')
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps('Handled ' + str(len(result)) + ' items !')
        }


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

        new_pending_list_pair = new_image.get(dynamodb.ACCOUNT_TABLE_ARCHIVE_PENDING_REQUEST_LIST)
        old_pending_list_pair = old_image.get(dynamodb.ACCOUNT_TABLE_ARCHIVE_PENDING_REQUEST_LIST)

        if new_pending_list_pair is None or old_pending_list_pair is None:
            continue
        
        new_pending_list = new_pending_list_pair.get('SS')
        old_pending_list = old_pending_list_pair.get('SS')

        if new_pending_list is None or old_pending_list is None:
            continue

        new_pending_set = set(new_pending_list)
        old_pending_set = set(old_pending_list)

        difference_set = new_pending_set.difference(old_pending_set)
        if len(difference_set) == 0:
            continue

        original_url = next(iter(difference_set))
        result.append((account_id, original_url))

    return result
