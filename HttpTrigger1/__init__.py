import os
import logging
from HttpTrigger1 import calcurate

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
    if state == 1:
        if req_body['events'][0]['message']['type'] == 'location':
            # DBに格納する値を変数に入れる
            req_loc = req_body['events'][0]['message']
            address = req_loc['address']
            latitude = req_loc['latitude']
            longitude = req_loc['longitude']
            title = "ごみ"

            # DBに格納
            garbage_tuple = (title, address, latitude, longitude)
            garbage_sql = """INSERT INTO garbage (title, address, latitude, longitude) VALUES (?, ?, ?, ?)"""
            cursor.execute(garbage_sql, garbage_tuple)
            conn.commit()

            text = '位置情報を登録しました'
        else:
            text = '最初からやり直してください'

        message = TextSendMessage(text=text)
        state = 0

    # 前回"探す"が入力されたとき(状態2)
    elif state == 2:
        if req_body['events'][0]['message']['type'] == 'location':
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
                text = '最初からやり直してください'
            )
        state = 0

    # 状態0の時
    elif state == 0:
        # もし送られてきたのが文字だったら
        if req_body['events'][0]['type'] == 'message':

            if req_body['events'][0]['message']['type'] == 'text':
                req_message = req_body['events'][0]['message']['text']

                if req_message == "登録":
                    state = 1
                    text = "位置情報を送ってください"
                elif req_message == "探す":
                    state = 2
                    text = "位置情報を送ってください"
                else:
                    state = 0
                    text = "登録or探す"

                message = TextSendMessage(text=text)
        # 文字以外の時
        else:
            message = TextSendMessage(
                text="aaaa"
            )

    # ユーザーの状態をDBに保存
    user_state = []
    user_state.append(user_id)
    user_state.append(state)
    state_taple = tuple(user_state)
    state_sql = """INSERT INTO state (user_id, state_num) VALUES (?, ?)"""
    cursor.execute(state_sql, state_taple)
    conn.commit()

    # 返信
    reply_token = req_body['events'][0]['replyToken']
    line_bot.reply_message(
        reply_token,
        message
    )

    return func.HttpResponse(
        "OK",
        status_code=200
    )
