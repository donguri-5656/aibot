import discord
from discord.ext import tasks
import requests
import os
import logging

# ログの設定（Renderの管理画面で動作を確認しやすくするため）
logging.basicConfig(level=logging.INFO)

# --- 設定項目（RenderのEnvironment Variablesで設定してください） ---
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
YT_API_KEY = os.environ.get('YOUTUBE_API_KEY')
YT_CHANNEL_ID = 'UCfcm9lIrkZcEwRf5Tne6_Bg'  # あなたのYouTubeチャンネルID
VC_ID = '1158354979313156111'              # 変更したいボイスチャンネルID

class MyBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        logging.info(f'Logged in as {self.user}')
        # ボットが起動したら定期更新タスクを開始
        if not self.update_loop.is_running():
            self.update_loop.start()

    @tasks.loop(minutes=15)
    async def update_loop(self):
        try:
            # 1. YouTube APIから統計情報を取得
            yt_url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics&id={YT_CHANNEL_ID}&key={YT_API_KEY}'
            res = requests.get(yt_url).json()
            
            if 'items' not in res:
                logging.error(f"YouTube API Error: {res}")
                return

            stats = res['items'][0]['statistics']
            subs = int(stats['subscriberCount'])
            views = int(stats['viewCount'])
            
            formatted_subs = "{:,}".format(subs)
            formatted_views = "{:,}".format(views)

            # 2. ボットのステータス（プレイ中）を更新
            # 例: 「総再生: 150,000回」をプレイ中
            status_text = f"総再生: {formatted_views}回"
            await self.change_presence(activity=discord.Game(name=status_text))
            logging.info(f"Status Updated: {status_text}")

            # 3. ボイスチャンネル名の更新
            # 例: 「👥 登録者: 2,000人」
            vc_name = f"👥 登録者: {formatted_subs}人"
            discord_url = f"https://discord.com/api/v10/channels/{VC_ID}"
            headers = {
                "Authorization": f"Bot {TOKEN}",
                "Content-Type": "application/json"
            }
            payload = {"name": vc_name}
            
            vc_res = requests.patch(discord_url, headers=headers, json=payload)
            if vc_res.status_code == 200:
                logging.info(f"VC Name Updated: {vc_name}")
            else:
                logging.error(f"VC Update Failed: {vc_res.text}")

        except Exception as e:
            logging.error(f"Error in update_loop: {e}")

# インテント（権限）の設定
intents = discord.Intents.default()
client = MyBot(intents=intents)

# 実行
if TOKEN:
    client.run(TOKEN)
else:
    logging.error("DISCORD_BOT_TOKEN が設定されていません。")
