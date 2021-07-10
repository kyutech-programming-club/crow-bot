import os
import logging

import azure.functions as func

from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, LocationSendMessage
)

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

line_bot = LineBotApi(ACCESS_TOKEN)
webhook_parser = WebhookParser(CHANNEL_SECRET)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    req_body = req.get_json()
    logging.info(req_body)

    if not req_body['events']:
        return func.HttpResponse(
           "OK",
            status_code=200
        )

    if req_body['events'][0]['type'] == 'message':
        reply_token = req_body['events'][0]['replyToken']

        if req_body['events'][0]['message']['type'] == 'location':
            message = TextSendMessage(
                text='位置情報を確認しました',
            )

        elif req_body['events'][0]['message']['type'] == 'text':
            req_message = req_body['events'][0]['message']['text']
            
            if req_message == "マップ":
                title = "東京タワー"
                address = "〒105-0011 東京都港区芝公園4-2-8"
                latitude = 35.658581
                longitude = 139.745433
                message = LocationSendMessage(
                    title=title,
                    address=address,
                    latitude=latitude,
                    longitude=longitude
                )
            else:
                message = TextSendMessage(
                    text="こんにちは"
                )

        else:
            message = TextSendMessage(
                text="aaaa"
            )

        line_bot.reply_message(
            reply_token,
            message
        )

    return func.HttpResponse(
        "OK",
        status_code=200
    )
