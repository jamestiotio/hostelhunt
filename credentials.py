# Store your credentials here
import os
import ast

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
MASTER_TOKEN = ast.literal_eval(os.environ['MASTER_TOKEN'])
ADMIN_LIST = ast.literal_eval(os.environ['ADMIN_LIST'])
SUTD_AUTH = ast.literal_eval(os.environ['SUTD_AUTH'])

PORT = int(os.environ.get('PORT', '5000'))
WEBHOOK_URL = os.environ['WEBHOOK_URL']
