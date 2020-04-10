import boto3
import botocore
import uuid


def print_dynamodb_response(response):
    import json
    import decimal
    class DecimalEncoder(json.JSONEncoder):
        # Helper class to convert a DynamoDB item to JSON.
        def default(self, o):
            if isinstance(o, decimal.Decimal):
                if abs(o) % 1 > 0:
                    return float(o)
                else:
                    return int(o)
            return super(DecimalEncoder, self).default(o)

    print(json.dumps(response, indent=4, cls=DecimalEncoder))


ACCOUNT_TABLE = 'arkAccount'
ARCHIVE_TABLE = 'arkArchive'


# Decorator for connecting to and disconnecting from the database
def dynamodb_operation(func):
    def inner(*args, **kwargs):
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        try:
            return func(dynamodb, *args, **kwargs)
        except Exception as e:
            print('Unexpected exception: ' + str(e))
    return inner


@dynamodb_operation
def create_new_account(dynamodb, username, password_hash, salt):
    '''
    salt must be a char[8]
    password_hash must be a char[64]
    Return error_message if errored; otherwise None
    '''
    error_message = None

    try:
        dynamodb.Table(ACCOUNT_TABLE).put_item(
            Item={
                'accountId': username,
                'passwordHash': password_hash,
                'passwordSalt': salt
            },
            ConditionExpression='attribute_not_exists(accountId)'
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            error_message = 'Error! ' + username + ' is already registered!'
        else:
            raise
    finally:
        return error_message


@dynamodb_operation
def get_account_credential(dynamodb, username):
    '''
    Return (password_hash, salt) if successful; otherwise None
    '''
    result = None

    response = dynamodb.Table(ACCOUNT_TABLE).get_item(
        Key={
            'accountId': username
        }
    )

    if response:
        item = response.get('Item')
        if item:
            result = (item['passwordHash'], item['passwordSalt'])
        return result


@dynamodb_operation
def create_account_table(dynamodb):
    '''
    Return True if successfully created; otherwise False
    '''
    try:
        dynamodb.create_table(
            TableName=ACCOUNT_TABLE,
            KeySchema=[
                {
                    'AttributeName': 'accountId',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'accountId',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
            }
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            return False
        else:
            raise
    else:
        return True


@dynamodb_operation
def clear_account_table(dynamodb):
    scan = None
    account_table = dynamodb.Table(ACCOUNT_TABLE)
    with account_table.batch_writer() as batch:
        while scan is None or 'LastEvaluatedKey' in scan:
            if scan is not None and 'LastEvaluatedKey' in scan:
                scan = account_table.scan(
                    ProjectionExpression='accountId',
                    ExclusiveStartKey=scan['LastEvaluatedKey'],
                )
            else:
                scan = account_table.scan(ProjectionExpression='accountId')

            for item in scan['Items']:
                batch.delete_item(Key={'accountId': item['accountId']})


@dynamodb_operation
def delete_table(dynamodb, table):
    dynamodb.Table(table).delete()


@dynamodb_operation
def get_table(dynamodb, table, return_raw=False):
    t = dynamodb.Table(table)

    response = t.scan()
    data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = t.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    if return_raw:
        return data
    else:
        return list(map(lambda item: tuple(item.values()), data))


@dynamodb_operation
def create_new_archive(dynamodb, url, date, username, datetime):
    '''
    Create a new archive entry.
    It is consisted of 2 items: main, archiveId. archiveId item is simply to make sure uniqueness of archiveId.
    Return True if new archive is created; False if the archive is already existed
    '''
    archive_table = dynamodb.Table(ARCHIVE_TABLE)

    # Check whether (url, date) exists
    try:
        archive_table.put_item(
            Item={
                'archiveUrl': url,
                'archiveDate': date,
                'createdAccountId': username,
                'createdDatetime': datetime,
                'modifiedAccountId': username,
                'modifiedDatetime': datetime
            },
            ConditionExpression='attribute_not_exists(archiveUrl) OR attribute_not_exists(archiveDate)'
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return False
        else:
            raise

    # Generate a unique id for the new archive
    while True:
        archive_id = str(uuid.uuid4())

        # Insert the archive_id to (url, date) primary index
        # in the format as: (url='archiveId#' + archiveId, date='archiveId#' + archiveId).
        # This is done to make sure the archiveId is unique.
            # Check whether (url, date) exists
        try:
            archive_table.put_item(
                Item={
                    'archiveUrl': 'archiveId#' + archive_id,
                    'archiveDate': 'archiveId#' + archive_id
                },
                ConditionExpression='attribute_not_exists(archiveUrl) OR attribute_not_exists(archiveDate)'
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                # archiveId is not unique, retry.
                # This won't happen alot (indeed, won't happen at all).
                continue
            else:
                raise

        # archive_id is unique, update the main item
        archive_table.update_item(
            Key={
                'archiveUrl': url,
                'archiveDate': date
            },
            UpdateExpression='set archiveId = :a',
            ExpressionAttributeValues={
                ':a': archive_id
            }
        )
        break
    
    return True


@dynamodb_operation
def get_archive_info(dynamodb, url, date):
    '''
    Return (archive_id, created_username, created_datetime, modified_username, modified_datetime) if found; otherwise None
    '''
    result = None

    response = dynamodb.Table(ARCHIVE_TABLE).get_item(
        Key={
            'archiveUrl': url,
            'archiveDate': date
        }
    )

    if response:
        item = response.get('Item')
        if item:
            result = (item['archiveId'], item['createdAccountId'], item['createdDatetime'], item['modifiedAccountId'], item['modifiedDatetime'])
        return result


@dynamodb_operation
def update_archive_info_timestamp(dynamodb, url, date, modified_username, modified_datetime):
    '''
    Return the (previous modified_username, previous modified_timestamp(datetime)) if updated successfully; None if entry is not existed yet
    '''
    
    previous_modified = None
    try:
        response = dynamodb.Table(ARCHIVE_TABLE).update_item(
            Key={
                'archiveUrl': url,
                'archiveDate': date
            },
            UpdateExpression='set modifiedAccountId = :a, modifiedDatetime = :d',
            ExpressionAttributeValues={
                ':a': modified_username,
                ':d': modified_datetime
            },
            ConditionExpression='attribute_exists(archiveUrl) AND attribute_exists(archiveDate)',
            ReturnValues='UPDATED_OLD'
        )

        previous_modified = (response['Attributes']['modifiedAccountId'], response['Attributes']['modifiedDatetime'])
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            pass
        else:
            raise
    finally:
        return previous_modified


@dynamodb_operation
def create_archive_table(dynamodb):
    '''
    Return True if successfully created; otherwise False
    '''
    try:
        dynamodb.create_table(
            TableName=ARCHIVE_TABLE,
            KeySchema=[
                {
                    'AttributeName': 'archiveUrl',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'archiveDate',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'archiveUrl',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'archiveDate',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
            }
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            return False
        else:
            raise
    else:
        return True


@dynamodb_operation
def clear_archive_table(dynamodb):
    scan = None
    archive_table = dynamodb.Table(ARCHIVE_TABLE)
    with archive_table.batch_writer() as batch:
        while scan is None or 'LastEvaluatedKey' in scan:
            if scan is not None and 'LastEvaluatedKey' in scan:
                scan = archive_table.scan(
                    ProjectionExpression='archiveUrl, archiveDate',
                    ExclusiveStartKey=scan['LastEvaluatedKey'])
            else:
                scan = archive_table.scan(ProjectionExpression='archiveUrl, archiveDate')

            for item in scan['Items']:
                batch.delete_item(Key={'archiveUrl': item['archiveUrl'], 'archiveDate': item['archiveDate']})
