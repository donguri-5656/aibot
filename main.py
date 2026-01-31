import discord
from discord.ext import tasks
import requests
import os

# --- 設定項目 ---
TOKEN = 'MTQ2NzA5MTk1MjkzODc4Mjg2Mg.GQ11CT.daLt_Z4_dg62iS3dFesDZLmF9j2qVkXRiL4GDQ'
YT_API_KEY = 'AIzaSyDdyBfVUr0tG17588sa8dQlOYdMVWDwibk'
YT_CHANNEL_ID = 'UCfcm9lIrkZcEwRf5Tne6_Bg'

class MyBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        self.update_status.start() # 定期実行開始

    @tasks.loop(minutes=15) # 15分ごとに更新
    async def update_status(self):
        try:
            # YouTube APIから再生回数を取得
            url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics&id={YT_CHANNEL_ID}&key={YT_API_KEY}'
            res = requests.get(url).json()
            views = res['items'][0]['statistics']['viewCount']
            formatted_views = "{:,}".format(int(views))
            
            # ステータス（プレイ中）を更新
            status_text = f"総再生: {formatted_views}回"
            await self.change_presence(activity=discord.Game(name=status_text))
            print(f'Status updated: {status_text}')
        except Exception as e:
            print(f'Error: {e}')

# インテントの設定（基本のみでOK）
intents = discord.Intents.default()
client = MyBot(intents=intents)
client.run(TOKEN)
