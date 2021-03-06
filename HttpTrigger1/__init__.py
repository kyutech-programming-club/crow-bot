import os
import logging
from HttpTrigger1 import calcurate

import sqlite3

import azure.functions as func

from linebot import (
    LineBotApi, WebhookParser
)
from linebot.models import (
    TextSendMessage,
    LocationSendMessage,
    TemplateSendMessage,
    MessageAction,
    ConfirmTemplate,
    LocationAction,
    ButtonsTemplate
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

    if state == 1 or state == 2:
        # DBからGarbageを取り出し
        garbage_sql = """SELECT * FROM garbage"""
        garbage_data = cursor.execute(garbage_sql)

    # 前回"登録"が入力されたとき(状態1)
    if state == 1:
        if req_body['events'][0]['message']['type'] == 'location':
            # DBに格納する値を変数に入れる
            req_loc = req_body['events'][0]['message']
            address = req_loc['address']
            latitude = req_loc['latitude']
            longitude = req_loc['longitude']
            title = "ごみ"

            if calcurate.omit_by_address(garbage_data, address):
            # DBに格納
                garbage_tuple = (title, address, latitude, longitude)
                garbage_sql = """INSERT INTO garbage (title, address, latitude, longitude) VALUES (?, ?, ?, ?)"""
                cursor.execute(garbage_sql, garbage_tuple)
                conn.commit()

                text = '位置情報を登録しました'
            else:
                text = 'すでに登録済みデータがあるようです'
        else:
            text = '最初からやり直してください'

        message = TextSendMessage(text=text)
        state = 0

    # 前回"探す"が入力されたとき(状態2)
    elif state == 2:
        if req_body['events'][0]['message']['type'] == 'location':
            # 一番近いゴミを取り出す
            req_loc = req_body['events'][0]['message']
            latitude = req_loc['latitude']
            longitude = req_loc['longitude']
            current_location = (latitude, longitude)
            garbage_tuple = calcurate.nearest_garbage(garbage_data, current_location)
            logging.info(garbage_tuple)
            # 取り出した位置情報を送信
            title = garbage_tuple[1]
            address = garbage_tuple[2]
            latitude = garbage_tuple[3]
            longitude = garbage_tuple[4]

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
        if req_body['events'][0]['message']['type'] == 'text':
            req_message = req_body['events'][0]['message']['text']

            if req_message == "登録":
                state = 1
            elif req_message == "探す":
                state = 2

        # 登録か探すが送られた時
        if state != 0:
            share_action = LocationAction(
                type="location",
                label="はい"
            )

            not_action = MessageAction(
                type="message",
                label="いいえ",
                text="いいえ"
            )

            default_action = share_action
            actions = [share_action, not_action]

            image_url = "https://raw.githubusercontent.com/kyutech-programming-club/crow-bot/image/gomi_karasu.png"

            buttons_temp = ButtonsTemplate(
                type="buttons",
                text="共有しますか？",
                title="位置情報",
                thumbnail_image_url=image_url,
                image_aspect_ratio="rectangle",
                image_size="cover",
                image_background_color="#FFFFFF",
                actions=actions,
                default_action=default_action
            )

            message = TemplateSendMessage(
                alt_text="This is a buttons template",
                template=buttons_temp
            )

        # もし登録か探す以外のものが送られた時
        else:
            ser_action = MessageAction(
                type="message",
                label="探す",
                text="探す"
            )

            regi_action = MessageAction(
                type="message",
                label="登録",
                text="登録"
            )

            default_action = ser_action
            actions = [ser_action, regi_action]

            image_url = "https://raw.githubusercontent.com/kyutech-programming-club/crow-bot/image/gomisuteba_kitanai.png"

            buttons_temp = ButtonsTemplate(
                type="buttons",
                title="ごみ",
                text="探す？登録する？",
                thumbnail_image_url=image_url,
                image_aspect_ratio="rectangle",
                image_size="cover",
                image_background_color="#FFFFFF",
                actions=actions,
                default_action=default_action
            )

            message = TemplateSendMessage(
                alt_text="This is a buttons template",
                template=buttons_temp
            )

    logging.info(message)

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
