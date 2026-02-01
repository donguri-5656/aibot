import discord
from discord.ext import tasks
import requests
import os
import logging
from flask import Flask
from threading import Thread
from datetime import datetime
import pytz

# ログの設定
logging.basicConfig(level=logging.INFO)

# --- Flask（GASからのアクセス受け取り用） ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- 設定項目 ---
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
YT_API_KEY = os.environ.get('YOUTUBE_API_KEY')
YT_CHANNEL_ID = 'UCfcm9lIrkZcEwRf5Tne6_Bg'
VC_ID = '1158354979313156111'
TIMEZONE = pytz.timezone('Asia/Tokyo')

class MyBot(discord.Client):
    async def on_ready(self):
        logging.info(f'Logged in as {self.user}')
        # ループ処理を開始
        if not self.update_status_loop.is_running():
            self.update_status_loop.start()
        if not self.update_vc_name_loop.is_running():
            self.update_vc_name_loop.start()

    # --- 15分ごとの処理：ステータス（プレイ中）の更新 ---
    @tasks.loop(minutes=15)
    async def update_status_loop(self):
        try:
            yt_url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics&id={YT_CHANNEL_ID}&key={YT_API_KEY}'
            res = requests.get(yt_url).json()
            views = int(res['items'][0]['statistics']['viewCount'])
            formatted_views = "{:,}".format(views)
            
            # 現在時刻を取得
            now = datetime.now(TIMEZONE).strftime('%H:%M')
            
            # ステータス表示（説明文付き）
            # 例：「総再生: 150,000回 (15分毎更新/14:30)」
            status_text = f"総再生: {formatted_views}回 ({now}更新/15分毎)"
            await self.change_presence(activity=discord.Game(name=status_text))
            logging.info(f"Status Updated: {status_text}")
        except Exception as e:
            logging.error(f"Status Update Error: {e}")

    # --- 30分ごとの処理：ボイスチャンネル名の更新 ---
    @tasks.loop(minutes=30)
    async def update_vc_name_loop(self):
        try:
            yt_url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics&id={YT_CHANNEL_ID}&key={YT_API_KEY}'
            res = requests.get(yt_url).json()
            subs = int(res['items'][0]['statistics']['subscriberCount'])
            formatted_subs = "{:,}".format(subs)
            
            vc_name = f"👥 登録者: {formatted_subs}人"
            discord_url = f"https://discord.com/api/v10/channels/{VC_ID}"
            headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}
            
            requests.patch(discord_url, headers=headers, json={"name": vc_name})
            logging.info(f"VC Name Updated: {vc_name} (30分間隔)")
        except Exception as e:
            logging.error(f"VC Update Error: {e}")

# インテント設定と実行
intents = discord.Intents.default()
client = MyBot(intents=intents)

keep_alive()
if TOKEN:
    client.run(TOKEN)
