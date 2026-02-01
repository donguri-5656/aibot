import discord
from discord.ext import tasks
import requests
import os
import logging
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
import asyncio
import pytz

logging.basicConfig(level=logging.INFO)

# --- Flask (Keep Alive) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"

def run_flask(): app.run(host='0.0.0.0', port=8080)

# --- 設定 ---
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
YT_API_KEY = os.environ.get('YOUTUBE_API_KEY')
YT_CHANNEL_ID = 'UCfcm9lIrkZcEwRf5Tne6_Bg'
VC_ID = '1158354979313156111'
GUILD_ID = 1158354979313156107 # あなたのサーバーID（数字）を入力してください
TIMEZONE = pytz.timezone('Asia/Tokyo')

class MyBot(discord.Client):
    async def on_ready(self):
        logging.info(f'Logged in as {self.user}')
        if not self.main_loop.is_running():
            self.main_loop.start()

    # キリのいい時間（00分, 30分）まで待機する関数
    async def wait_until_next_interval(self):
        now = datetime.now(TIMEZONE)
        if now.minute < 30:
            target = now.replace(minute=30, second=0, microsecond=0)
        else:
            target = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        
        wait_seconds = (target - now).total_seconds()
        logging.info(f"Next update at {target.strftime('%H:%M')}. Waiting {wait_seconds} seconds.")
        await asyncio.sleep(wait_seconds)

    @tasks.loop(minutes=30)
    async def main_loop(self):
        # 最初の1回目だけ、キリのいい時間まで待つ
        if not hasattr(self, 'first_run_done'):
            await self.wait_until_next_interval()
            self.first_run_done = True

        try:
            # 1. YouTubeデータ取得
            yt_url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics&id={YT_CHANNEL_ID}&key={YT_API_KEY}'
            res = requests.get(yt_url).json()
            stats = res['items'][0]['statistics']
            
            views = "{:,}".format(int(stats['viewCount']))
            subs = "{:,}".format(int(stats['subscriberCount']))
            
            # 2. サーバーでのニックネームを変更 (Botの名前を総再生数に)
            guild = self.get_guild(GUILD_ID)
            if guild:
                try:
                    await guild.me.edit(nick=f"総再生: {views}回")
                    logging.info("Nickname updated.")
                except Exception as e:
                    logging.error(f"Nickname update failed: {e}")

            # 3. ボイスチャンネル名を更新
            headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}
            requests.patch(f"https://discord.com/api/v10/channels/{VC_ID}", 
                           headers=headers, json={"name": f"👥 登録者: {subs}人"})

            # 4. ステータス（プレイ中）を更新
            # 次回更新時刻を計算して表示
            next_time = (datetime.now(TIMEZONE) + timedelta(minutes=30)).strftime('%H:%M')
            status_text = f"次回更新: {next_time}頃 (30分毎)"
            await self.change_presence(activity=discord.Game(name=status_text))

        except Exception as e:
            logging.error(f"Loop Error: {e}")

intents = discord.Intents.default()
intents.members = True # ニックネーム変更に必要
client = MyBot(intents=intents)

Thread(target=run_flask).start()
if TOKEN:
    client.run(TOKEN)
