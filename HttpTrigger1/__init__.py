import os
import logging

import sqlite3

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
    # データベースの設定
    dbname = ('crow.db')
    conn = sqlite3.connect(dbname, isolation_level=None)
    cursor = conn.cursor()

    garbage_sql = """CREATE TABLE IF NOT EXISTS garbage(id INTEGER PRIMARY KEY AUTOINCREMENT, title, address, latitude, longitude)"""
    state_sql = """CREATE TABLE IF NOT EXISTS state(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id, state_num)"""

    cursor.execute(garbage_sql)
    conn.commit()
    cursor.execute(state_sql)
    conn.commit()

    logging.info('Python HTTP trigger function processed a request.')

    # リクエストをjsonで取得
    req_body = req.get_json()
    logging.info(req_body)

    # イベントがちゃんとしてなかった時
    if not req_body['events']:
        return func.HttpResponse(
           "OK",
            status_code=200
        )

    # ユーザーの状態を取得する
    user_id = req_body['events'][0]['source']['userId']
    state_sql = """SELECT state_num FROM state WHERE user_id=? ORDER BY id DESC LIMIT 1"""
    state_data = cursor.execute(state_sql, (user_id,))

    cnt = 0
    for user_state in state_data:
        state = user_state[0]
        cnt += 1

    if cnt == 0:
        state = 0

    # 前回"登録"が入力されたとき(状態1)

    # 前回"探す"が入力されたとき(状態2)

    # 状態0の時
    # もし送られてきたのが文字だったら
    if req_body['events'][0]['type'] == 'message':
        reply_token = req_body['events'][0]['replyToken']

        if req_body['events'][0]['message']['type'] == 'text':
            req_message = req_body['events'][0]['message']['text']
            user_state = []
            user_state.append(user_id)

            if req_message == "登録":
                state = 1
            elif req_message == "探す":
                state = 2
            else:
                state = 0
                message = TextSendMessage(
                    text="こんにちは"
                )

            user_state.append(state)
            state_taple = tuple(user_state)
            state_sql = """INSERT INTO state (user_id, state_num) VALUES (?, ?)"""
            cursor.execute(state_sql, state_taple)
            conn.commit()

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
