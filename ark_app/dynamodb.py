import boto3
import botocore


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


_ACCOUNT_TABLE = 'arkAccount'


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
        dynamodb.Table(_ACCOUNT_TABLE).put_item(
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

    response = dynamodb.Table(_ACCOUNT_TABLE).get_item(
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
def delete_account_table(dynamodb):
    dynamodb.Table(_ACCOUNT_TABLE).delete()


@dynamodb_operation
def create_account_table(dynamodb):
    '''
    Return True if successfully created; otherwise False
    '''
    try:
        dynamodb.create_table(
            TableName=_ACCOUNT_TABLE,
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
    account_table = dynamodb.Table(_ACCOUNT_TABLE)
    with account_table.batch_writer() as batch:
        count = 0
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
                count = count + 1


@dynamodb_operation
def get_account_table(dynamodb, return_raw=False):
    account_table = dynamodb.Table(_ACCOUNT_TABLE)

    response = account_table.scan()
    data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = account_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    if return_raw:
        return data
    else:
        return list(map(lambda item: tuple(item.values()) ,data))
