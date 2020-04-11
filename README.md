# ark
[Requirements](http://www.cs.toronto.edu/~delara/courses/ece1779/projects/ECE1779-a3.pdf)


## 1.0 Ark App


### 1.1 Business Logics


### 1.1.1 Frontend
The behaviour of the application follows the following two rules:
1. Searches by URL, followed with gradually fine-grained timestamp prompt. The latest
result from each timestamp-granualarity is shown
2. Archives URL. Does not show any updates immediaty, successfully-archived sites
will be shown via message list.

Currently: users must login to be able to use the application.  
Planning: users that are not logged in can only do searchings, but not any archivings.


### 1.1.2 Backend
Flask: Users must login to do archivings. Once the http request is received by the flask server,
it stores the original url request into arkAccount.archivePendingRequestList.

Once there are insertions into arkAccount.archivePendingRequestList, amazon Lambda is triggered.

Amazon Lambda: The main archiving algorithm starts to process the new request from arkAccount.archivePendingRequestList 
by removing the request from the list first. It firstly tries to normalize the url, then tries to fix the 
url if the url is missing 'HTTP' or 'HTTPS'. Then it creates a formal archive entry in arkArchive, and takes
a screenshot for the webpage which is stored to S3. If the above process fails, the request is moved to
arkAccount.archiveFailedRequestList for notifying the user.

Flask: Upon user login, arkAccount.archiveFailedRequestList, arkAccount.archivePendingRequestList and
the latest several submitted histories are shown.


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
pip install archiveis
pip install bs4

python run_ark_app.py
```


#### 1.2.2 chromedriver Setup
Located in `archivelib/chromedrivers`  
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


### 1.3 AWS


#### 1.3.1 Packages
AWS Lambda for archive: ```corelib``` and ```archivelib```  
AWS Lambda for flask zappa (as_handler.RUNNING_LOCALLY == False): ```corelib``` and ```ark_app```


### 1.4 Management Script


#### 1.4.1 Helper
Manage DynamoDB and S3 contents locally.
```
python helper.py --help
```
