import os
import logging

import azure.functions as func

from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage
)

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

line_bot = LineBotApi()

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    req_body = req.get_json()
    logging.info(req_body)

    return func.HttpResponse(
        "OK",
        status_code=200
    )
