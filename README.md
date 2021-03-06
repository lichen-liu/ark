# Ark
A place for you to screenshot and store your favourite websites like a charm.

~~[Requirements](http://www.cs.toronto.edu/~delara/courses/ece1779/projects/ECE1779-a3.pdf)~~

Try it [here](https://ahiptn0b0k.execute-api.us-east-1.amazonaws.com/dev/main)


# 1. Architecture


## 1.1 Overview
The project makes use of various AWS services for execution and backend data storage.
* AWS S3: URL Website screenshot storage
* AWS DynamoDB: Database
* AWS Lambda:
  - Flask HTTP Server
  - Archiver Lambda Function


## 1.2 Frontend UI Logics
The behaviour of the application follows the following two rules:
1. Searches by URL, followed with gradually fine-grained timestamp prompt. The latest
result from each timestamp-granualarity is shown
2. Archives URL. Does not show any updates immediaty, successfully-archived sites
will be shown via message list.

Currently: users must login to be able to use the application.  
Planning: users that are not logged in can only do searchings, but not any archivings.


## 1.3 Main Business Logics Implementation Logics
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


# 2. Local Deployment


## 2.1 Python Setup
Use: Python 3.7.3
```
python -m venv venv

venv\Scripts\activate
source venv/bin/activate

# Not required for corelib and archivelib
pip install Flask

# Required for all
pip install boto3
pip install Pillow
pip install selenium
pip install requests
pip install archiveis
pip install bs4

python run_ark_app.py
```


## 2.2 chromedriver Setup
Located in `archivelib/chromedrivers`  
Win32: Chrome version 81  
Mac64: Chrome version


## 2.3 AWS Credential Setup
Set ~/.aws/credentials following this format:

```
[default]
aws_access_key_id= Your_aws_access_key_id
aws_secret_access_key= Your_aws_access_key
aws_session_token= Your_session_token
```


# 3. AWS Deployment
https://ahiptn0b0k.execute-api.us-east-1.amazonaws.com/dev/main

**If not using ```helper.py``` to deploy,**  
**set the following in ```ark_app/config.py```**
```
config.RUNNING_LOCALLY = False
```

Requires the following packages
```
pip install zappa
```


## 3.1 Packages
AWS Lambda for archive: ```corelib``` and ```archivelib```  
AWS Lambda for flask zappa: ```corelib``` and ```ark_app```


## 3.2 Deployment
Use the helper script to do all AWS deployment automatically.
```
python helper.py --update_resources --update_archiver --update_flask
```


## 3.3 Zappa
*Currently, only `dev` branch is deployed*
To deploy
```
zappa deploy dev
```
To update
```
zappa update dev
```
To undeploy
```
zappa undeploy dev
```


## 3.4 Lambda
Uses ```serverless-chrome```: https://github.com/adieuadieu/serverless-chrome


To upload Lambda Function Code, upload build.zip to S3, and update in Lambda
```
build.zip
    src - (corelib, archivelib, lambda_function_archiver.py)
    lib - Python Libraries
    bin - Executables (serverless-chrome, chromedriver, .font)
```


To get `lib`, Use Python 3.7.3 and do the following
```
pip install boto3 -t . --no-compile --platform=manylinux1_x86_64 --only-binary=:all:
pip install Pillow -t . --no-compile --platform=manylinux1_x86_64 --only-binary=:all:
pip install selenium -t . --no-compile --platform=manylinux1_x86_64 --only-binary=:all:
pip install requests -t . --no-compile --platform=manylinux1_x86_64 --only-binary=:all:
pip install archiveis -t . --no-compile --platform=manylinux1_x86_64 --only-binary=:all:
pip install bs4 -t . --no-compile
```


Fonts are stored in ```bin/.font```, downloaded from https://github.com/googlefonts/noto-cjk   
Currently, only ```.otf``` fonts are tested.


Set the following environment variable:
```
PYTHONPATH	/var/task/src:/var/task/lib
HOME	/var/task/bin
```


Properly set triggers, permissions, restrictions.


## 3.5 Static Resources
Update all local static/icons to S3
```
python helper.py --update_resources
```
