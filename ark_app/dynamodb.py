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


# Table names
ACCOUNT_TABLE = 'arkAccount'
ARCHIVE_TABLE = 'arkArchive'

# Index names
ARCHIVE_TABLE_GSI_ARCHIVE_ACCOUNT_ID_ARCHIVE_URL = ARCHIVE_TABLE + 'GSIByArchiveAccountIdArchiveUrl'

# archive Request Lists
ACCOUNT_TABLE_ARCHIVE_PENDING_REQUEST_LIST = 'archivePendingRequestList'
ACCOUNT_TABLE_ARCHIVE_FAILED_REQUEST_LIST = 'archiveFailedRequestList'


def dynamodb_resource_operation(func):
    def inner(*args, **kwargs):
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        try:
            return func(dynamodb, *args, **kwargs)
        except Exception as e:
            print('Unexpected exception: ' + str(e))
    return inner


def dynamodb_client_operation(func):
    def inner(*args, **kwargs):
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        try:
            return func(dynamodb, *args, **kwargs)
        except Exception as e:
            print('Unexpected exception: ' + str(e))
    return inner


@dynamodb_resource_operation
def create_new_account(dynamodb, username, password_hash, salt):
    '''
    salt must be a char[8]
    password_hash must be a char[64]
    Return error_message if errored; otherwise None
    '''
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
            return 'Error! ' + username + ' is already registered!'
        else:
            raise


@dynamodb_resource_operation
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


@dynamodb_client_operation
def push_account_archive_request(dynamodb, list_name, username, original_url):
    dynamodb.update_item(
        TableName=ACCOUNT_TABLE,
        Key={
            'accountId': {'S': username}
        },
        UpdateExpression='add ' + list_name + ' :original_url',
        ExpressionAttributeValues={
            ':original_url': {'SS': [original_url]}
        },
        ConditionExpression='attribute_exists(accountId)'
    )


@dynamodb_client_operation
def pop_account_archive_request_by(dynamodb, list_name, username, original_url):
    '''
    Return True if successfully found and deleted original_url; return False otherwise
    '''
    try:
        dynamodb.update_item(
            TableName=ACCOUNT_TABLE,
            Key={
                'accountId': {'S': username}
            },
            UpdateExpression='delete ' + list_name + ' :original_urls',
            ExpressionAttributeValues={
                ':original_urls': {'SS': [original_url]},
                ':original_url': {'S': original_url}
            },
            ConditionExpression='attribute_exists(accountId) AND attribute_exists(' + list_name + ') AND contains(' + list_name + ', :original_url)'
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return False
        else:
            raise
    
    return True


@dynamodb_resource_operation
def clear_account_archive_request_by(dynamodb, list_name, username):
    try:
        dynamodb.Table(ACCOUNT_TABLE).update_item(
            Key={
                'accountId': username
            },
            UpdateExpression='remove ' + list_name,
            ConditionExpression='attribute_exists(accountId) AND attribute_exists(' + list_name + ')'
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            pass
        else:
            raise


@dynamodb_resource_operation
def get_account_archive_request_list(dynamodb, list_name, username):
    '''
    Return [original_url] if found; otherwise None
    '''
    try:
        response=dynamodb.Table(ACCOUNT_TABLE).get_item(
            Key={
                'accountId': username
            },
            ProjectionExpression=list_name
        )
        item = response.get('Item')
        if item:
            return item[list_name]

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return None
        else:
            raise


@dynamodb_resource_operation
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


@dynamodb_resource_operation
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


@dynamodb_resource_operation
def delete_table(dynamodb, table):
    dynamodb.Table(table).delete()


@dynamodb_resource_operation
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


@dynamodb_resource_operation
def create_new_archive(dynamodb, url, datetime, username, archive_md_url):
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
                'archiveDatetime': datetime,
                'archiveAccountId': username,
                'archiveMDUrl': archive_md_url
            },
            ConditionExpression='attribute_not_exists(archiveUrl) OR attribute_not_exists(archiveDatetime)'
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
                    'archiveDatetime': 'archiveId#' + archive_id
                },
                ConditionExpression='attribute_not_exists(archiveUrl) OR attribute_not_exists(archiveDatetime)'
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
                'archiveDatetime': datetime
            },
            UpdateExpression='set archiveId = :a',
            ExpressionAttributeValues={
                ':a': archive_id
            }
        )
        break
    
    return True


@dynamodb_resource_operation
def get_archive_info(dynamodb, url, datetime):
    '''
    Return (archive_id, username, archive_md_url) if found; otherwise None
    '''
    result = None

    response = dynamodb.Table(ARCHIVE_TABLE).get_item(
        Key={
            'archiveUrl': url,
            'archiveDatetime': datetime
        }
    )

    if response:
        item = response.get('Item')
        if item:
            result = (item['archiveId'], item['archiveAccountId'], item['archiveMDUrl'])
        return result


@dynamodb_client_operation
def search_archive_by_url(dynamodb, url, by_date=None):
    '''Get Primary Sort Keys by filtering the Primary Range Key(url)
    
    by_date = datetime.date(), search only for this date
    [datetime], sorted from latest to oldest
    '''
    result = list()
    response = None

    while response is None or 'LastEvaluatedKey' in response:
        if response is not None and 'LastEvaluatedKey' in response:
            if by_date:
                response = dynamodb.query(
                    TableName=ARCHIVE_TABLE,
                    KeyConditionExpression='archiveUrl = :url and begins_with(archiveDatetime, :by_date)',
                    ExpressionAttributeValues={
                        ':url': {'S': url},
                        ':by_date': {'S': str(by_date)}
                    },
                    ProjectionExpression='archiveDatetime',
                    ScanIndexForward=False,
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
            else:
                response = dynamodb.query(
                    TableName=ARCHIVE_TABLE,
                    KeyConditionExpression='archiveUrl = :url',
                    ExpressionAttributeValues={
                        ':url': {'S': url}
                    },
                    ProjectionExpression='archiveDatetime',
                    ScanIndexForward=False,
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
        else:
            if by_date:
                response = dynamodb.query(
                    TableName=ARCHIVE_TABLE,
                    KeyConditionExpression='archiveUrl = :url and begins_with(archiveDatetime, :by_date)',
                    ExpressionAttributeValues={
                        ':url': {'S': url},
                        ':by_date': {'S': str(by_date)}
                    },
                    ProjectionExpression='archiveDatetime',
                    ScanIndexForward=False
                )
            else:
                response = dynamodb.query(
                    TableName=ARCHIVE_TABLE,
                    KeyConditionExpression='archiveUrl = :url',
                    ExpressionAttributeValues={
                        ':url': {'S': url}
                    },
                    ProjectionExpression='archiveDatetime',
                    ScanIndexForward=False
                )
    
        items = response.get('Items')
        result.extend(map(lambda item: item['archiveDatetime']['S'], items))
    
    return result


@dynamodb_client_operation
def search_archive_by_username(dynamodb, username, num_latest_archive=None):
    '''
    if num_latest_archive is None, return all matching archives
    [(url, datetime)], sorted from latest to oldest
    '''
    result = list()
    response = None

    while response is None or 'LastEvaluatedKey' in response:
        if response is not None and 'LastEvaluatedKey' in response:
            response = dynamodb.query(
                TableName=ARCHIVE_TABLE,
                IndexName=ARCHIVE_TABLE_GSI_ARCHIVE_ACCOUNT_ID_ARCHIVE_URL,
                KeyConditionExpression='archiveAccountId = :username',
                ExpressionAttributeValues={
                    ':username': {'S': username}
                },
                ProjectionExpression='archiveUrl, archiveDatetime',
                ScanIndexForward=False,
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
        else:
            response = dynamodb.query(
                TableName=ARCHIVE_TABLE,
                IndexName=ARCHIVE_TABLE_GSI_ARCHIVE_ACCOUNT_ID_ARCHIVE_URL,
                KeyConditionExpression='archiveAccountId = :username',
                ExpressionAttributeValues={
                    ':username': {'S': username}
                },
                ProjectionExpression='archiveUrl, archiveDatetime',
                ScanIndexForward=False
            )

        items = response.get('Items')
        result.extend(map(lambda item: (item['archiveUrl']['S'], item['archiveDatetime']['S']), items))

        if num_latest_archive:
            if len(result) >= num_latest_archive:
                return result[:num_latest_archive]

    return result


@dynamodb_resource_operation
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
                    'AttributeName': 'archiveDatetime',
                    'KeyType': 'RANGE'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': ARCHIVE_TABLE_GSI_ARCHIVE_ACCOUNT_ID_ARCHIVE_URL,
                    'KeySchema': [
                        {
                            'AttributeName': 'archiveAccountId',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'archiveDatetime',
                            'KeyType': 'RANGE'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'archiveUrl',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'archiveDatetime',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'archiveAccountId',
                    'AttributeType': 'S'
                },
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


@dynamodb_resource_operation
def clear_archive_table(dynamodb):
    scan = None
    archive_table = dynamodb.Table(ARCHIVE_TABLE)
    with archive_table.batch_writer() as batch:
        while scan is None or 'LastEvaluatedKey' in scan:
            if scan is not None and 'LastEvaluatedKey' in scan:
                scan = archive_table.scan(
                    ProjectionExpression='archiveUrl, archiveDatetime',
                    ExclusiveStartKey=scan['LastEvaluatedKey'])
            else:
                scan = archive_table.scan(ProjectionExpression='archiveUrl, archiveDatetime')

            for item in scan['Items']:
                batch.delete_item(Key={'archiveUrl': item['archiveUrl'], 'archiveDatetime': item['archiveDatetime']})


@dynamodb_client_operation
def get_estimated_num_archives(dynamodb):
    '''
    The number of items in the specified table. DynamoDB updates this value approximately every six hours. Recent changes might not be reflected in this value.
    '''
    response = dynamodb.describe_table(TableName=ARCHIVE_TABLE)
    # A single archive entry occupies two rows
    return int(response['Table']['ItemCount'] / 2)


@dynamodb_client_operation
def get_estimated_num_users(dynamodb):
    '''
    The number of items in the specified table. DynamoDB updates this value approximately every six hours. Recent changes might not be reflected in this value.
    '''
    response = dynamodb.describe_table(TableName=ACCOUNT_TABLE)
    return response['Table']['ItemCount']