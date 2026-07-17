import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import time

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('BOT_PREFIX', '^')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=f"{PREFIX}komutlar | XERM BOT MANAGER"))
    print(f'---')
    print(f'Bot Giriş Yaptı: {bot.user.name}')
    print(f'ID: {bot.user.id}')
    print(f'{bot.user} olarak giriş yapıldı!')
    print(f'Kullanılan önek: "{PREFIX}"')
    print(f'---')


@bot.command(name='test')
async def test(ctx):
    embed = discord.Embed(
        title="Bot Aktif",
        description="Bot başarıyla çalışıyor!",
        color=0x57F287
    )
    embed.add_field(name="Gecikme", value=f"**{round(bot.latency * 1000)}ms**", inline=True)
    embed.add_field(name="Bot Adı", value=f"{bot.user.name}", inline=True)
    embed.add_field(name="Önek", value=f"`{PREFIX}`", inline=True)
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    await ctx.send(embed=embed)


@bot.command(name='ping')
async def ping(ctx):
    await ctx.send(f"Pong! **{round(bot.latency * 1000)}ms**")


@bot.command(name='komutlar')
async def komutlar(ctx):
    komutlar = []
    for cmd in sorted(bot.commands, key=lambda c: c.name):
        aciklama = cmd.help or "Açıklama yok"
        komutlar.append(f"**{PREFIX}{cmd.name}** — {aciklama}")

    aciklama = "\n".join(komutlar) if komutlar else "Henüz komut yok."
    embed = discord.Embed(
        title="Komut Listesi",
        description=aciklama,
        color=0x5865F2
    )
    embed.set_footer(text=f"Toplam {len(komutlar)} komut")
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    await ctx.send(embed=embed)


@bot.command(name='uptime')
async def uptime(ctx):
    start = time.time()
    msg = await ctx.send("Ölçülüyor...")
    end = time.time()
    await msg.edit(content=f"API Gecikmesi: **{round(bot.latency * 1000)}ms**\nMesaj Gecikmesi: **{round((end - start) * 1000)}ms**")


if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("HATA: .env dosyasında 'DISCORD_TOKEN' bulunamadı!")
