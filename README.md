# ark
[Requirements](http://www.cs.toronto.edu/~delara/courses/ece1779/projects/ECE1779-a3.pdf)


## 1.0 Ark App


### 1.1 Local
Use: Python 3.7.3
```
python -m venv venv
venv\Scripts\activate
source venv/bin/activate
pip install Flask
pip install boto3
pip install requests

python run_ark_app.py
```

Then set ~/.aws/credentials following this format:

```
[default]
aws_access_key_id= Your_aws_access_key_id
aws_secret_access_key= Your_aws_access_key
aws_session_token= Your_session_token
```

To get the above values (key_id, key, token),and for an AWS educate account, it will be at your AWS Educate Account page -> Account Details.
