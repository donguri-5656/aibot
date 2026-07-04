import os
import threading
import asyncio
import discord
from discord.ext import commands
from gradio_client import Client
from fastapi import FastAPI

# FastAPIの起動（Renderの「Web Service」を維持するためのダミーWeb画面）
app = FastAPI()
@app.get("/")
def read_root():
    return {"status": "running"}

# Discordボットの設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Hugging FaceのAPIクライアントを設定
HF_SPACE_URL = os.getenv("HF_SPACE_URL") # 例: https://hf.space
hf_client = Client(HF_SPACE_URL) if HF_SPACE_URL else None

@bot.event
async def on_ready():
    print(f"Render側でログインしました: {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if not prompt:
            await message.channel.send("なにか話しかけてね！")
            return

        async with message.channel.typing():
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: hf_client.predict(prompt)
                )
                await message.channel.send(result)
            except Exception as e:
                print(f"エラーが発生しました: {e}")
                await message.channel.send("ごめん、うまく聞き取れなかったよ。")

# ボットをバックグラウンドで動かす
def run_discord_bot():
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)

if __name__ == "__main__":
    # Discordボットを別スレッドで起動
    threading.Thread(target=run_discord_bot, daemon=True).start()
    
    # Render用にWebサーバーを起動
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
