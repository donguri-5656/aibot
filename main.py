import discord
from discord.ext import tasks
import requests
import os
import logging
from flask import Flask
from threading import Thread

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

# --- Discord Bot部分 ---
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
YT_API_KEY = os.environ.get('YOUTUBE_API_KEY')
YT_CHANNEL_ID = 'UCfcm9lIrkZcEwRf5Tne6_Bg'
VC_ID = '1158354979313156111'

class MyBot(discord.Client):
    async def on_ready(self):
        logging.info(f'Logged in as {self.user}')
        if not self.update_loop.is_running():
            self.update_loop.start()

    @tasks.loop(minutes=15)
    async def update_loop(self):
        try:
            yt_url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics&id={YT_CHANNEL_ID}&key={YT_API_KEY}'
            res = requests.get(yt_url).json()
            stats = res['items'][0]['statistics']
            
            # ステータス更新
            views = "{:,}".format(int(stats['viewCount']))
            await self.change_presence(activity=discord.Game(name=f"総再生: {views}回"))
            
            # VC名更新
            subs = "{:,}".format(int(stats['subscriberCount']))
            requests.patch(f"https://discord.com/api/v10/channels/{VC_ID}", 
                           headers={"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"},
                           json={"name": f"👥 登録者: {subs}人"})
        except Exception as e:
            logging.error(f"Error: {e}")

# インテント設定と実行
intents = discord.Intents.default()
client = MyBot(intents=intents)

keep_alive() # Flaskを別スレッドで起動
if TOKEN:
    client.run(TOKEN)
