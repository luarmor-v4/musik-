import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

# ═══════════════════════════════════════
# SETUP REPLIT & TOKEN
# ═══════════════════════════════════════
# Ambil token dari Secrets (Environment Variables) di Replit agar aman
TOKEN = os.environ['DISCORD_TOKEN'] 

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ═══════════════════════════════════════
# KONFIGURASI MUSIK
# ═══════════════════════════════════════
yt_dl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # Wajib untuk Replit agar IP tidak diblokir
}

ffmpeg_options = {
    'options': '-vn',
    # Reconnect wajib agar bot tidak mati di tengah lagu karena internet server
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(yt_dl_opts)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# ═══════════════════════════════════════
# EVENTS & COMMANDS
# ═══════════════════════════════════════
@bot.event
async def on_ready():
    print(f'✅ Bot Musik {bot.user.name} Online di Replit!')

@bot.command(name='play')
async def play(ctx, *, search: str):
    # Cek user di voice channel
    if not ctx.author.voice:
        return await ctx.send("❌ Masuk voice channel dulu dong!")

    # Bot join
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()
    
    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(search, loop=bot.loop, stream=True)
            
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
                
            ctx.voice_client.play(player, after=lambda e: print(f'Error: {e}') if e else None)
            await ctx.send(f'🎶 **Memutar:** {player.title}')
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Bye!")

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")

# Jalankan (Pastikan Token ada di Secrets Replit)
bot.run(TOKEN)
