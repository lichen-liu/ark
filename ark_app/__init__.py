from flask import Flask

webapp = Flask(__name__)

webapp.config.from_object('ark_app.config.Config')

from ark_app import main, account, archiver, searcher

from ark_app import initialize
initialize.init()