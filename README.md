# ark
[Requirements](http://www.cs.toronto.edu/~delara/courses/ece1779/projects/ECE1779-a3.pdf)


## 1.0 Ark App


### 1.1 Local


#### 1.1.1 Python Setup
Use: Python 3.7.3
```
python -m venv venv
venv\Scripts\activate
source venv/bin/activate
pip install Flask
pip install boto3
pip install Pillow
pip install selenium

python run_ark_app.py
```


#### 1.1.2 chromedriver Setup
Located in `ark_app/chromedrivers`
Win32: Chrome version 81
Mac64: Chrome version


#### 1.1.3 AWS Credential Setup
Set ~/.aws/credentials following this format:

```
[default]
aws_access_key_id= Your_aws_access_key_id
aws_secret_access_key= Your_aws_access_key
aws_session_token= Your_session_token
```

To get the above values (key_id, key, token),and for an AWS educate account, it will be at your AWS Educate Account page -> Account Details.
