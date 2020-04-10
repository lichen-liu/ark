# Don't touch dynamodb.py, modification in progress for user-notification support


# ark
[Requirements](http://www.cs.toronto.edu/~delara/courses/ece1779/projects/ECE1779-a3.pdf)


## 1.0 Ark App


### 1.1 Business Logics


### 1.1.1 Frontend
The behaviour of the application follows the following two rules:
1. If searching for archives from the past, return if found, try to search the archive from today otherwise.
2. If searching for archives from today, return if found, archive it otherwise. Supports forcefully re-archiving 
for today's snapshot.

Currently: users must login to be able to use the application.  
Planning: users that are not logged in can only do searchings, but not any archivings.


### 1.1.2 Backend
Flask: Users must login to do archivings. Once the http request is received by the flask server,
it stores the original url request into arkAccount.requestList.

Once there are insertions into arkAccount.requestList, amazon Lambda is triggered.

Amazon Lambda: The main archiving algorithm starts to process the new request from arkAccount.requestList 
by removing the request from the list first. It firstly tries to normalize the url, then tries to fix the 
url if the url is missing 'HTTP' or 'HTTPS'. Then it creates a formal archive entry in arkArchive, and takes
a screenshot for the webpage which is stored to S3. Regardless of whether the above process fails or not,
the request is moved to arkAccount.responseList for notifying the user.

Flask: Upon user login, responses from arkAccount.responseList are shown. Users then must explicitly 
close the notification for each reponse. This will notify the Flask server to remove those responses from
arkAccount.responseList.


### 1.2 Local


#### 1.2.1 Python Setup
Use: Python 3.7.3
```
python -m venv venv
venv\Scripts\activate
source venv/bin/activate
pip install Flask
pip install boto3
pip install Pillow
pip install selenium
pip install requests

python run_ark_app.py
```


#### 1.2.2 chromedriver Setup
Located in `ark_app/chromedrivers`  
Win32: Chrome version 81  
Mac64: Chrome version


#### 1.2.3 AWS Credential Setup
Set ~/.aws/credentials following this format:

```
[default]
aws_access_key_id= Your_aws_access_key_id
aws_secret_access_key= Your_aws_access_key
aws_session_token= Your_session_token
```


### 1.4 Management Script


#### 1.4.1 Helper
Manage DynamoDB and S3 contents locally.
```
python ark_app/helper.py --help
```
