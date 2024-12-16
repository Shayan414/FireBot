import discord
from discord.ext import commands
import yt_dlp
import random
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Queue to manage songs
song_queue = []

@bot.event
async def on_ready():
    print(f"{bot.user} has connected!")

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("Joined the voice channel!")
    else:
        await ctx.send("You need to be in a voice channel first.")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Left the voice channel!")
    else:
        await ctx.send("I'm not in a voice channel.")

@bot.command()
async def play(ctx, *, search_query):
    """Plays music from a YouTube URL or searches YouTube for a query."""
    if not ctx.voice_client:
        await ctx.invoke(join)

    voice_client = ctx.voice_client

    # Check if the input is a URL or a search query
    if "youtube.com" in search_query or "youtu.be" in search_query:
        url = search_query
    else:
        await ctx.send(f"Searching for: {search_query}")
        url = search_youtube(search_query)

    if not voice_client.is_playing():
        info = get_video_info(url)
        if info:
            await ctx.send(f"Playing: {info['title']}")
            play_music(voice_client, url)
        else:
            await ctx.send("Could not find the video.")
    else:
        song_queue.append(url)
        await ctx.send(f"Added to queue: {url}")

def search_youtube(query):
    """Searches YouTube and returns the URL of the first video result."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch',
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info and len(info['entries']) > 0:
            first_result = info['entries'][0]
            return first_result['url']
        else:
            return None

def get_video_info(url):
    """Fetches video info such as title."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {"title": info.get("title"), "url": info.get("url")} if info else None

def play_music(voice_client, url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['url']
        source = discord.FFmpegPCMAudio(url2)
        voice_client.play(source, after=lambda e: check_queue(voice_client))

def check_queue(voice_client):
    if song_queue:
        next_song = song_queue.pop(0)
        play_music(voice_client, next_song)

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped!")
    else:
        await ctx.send("No song is currently playing.")

@bot.command()
async def queue(ctx):
    if song_queue:
        queue_list = "\n".join([f"{idx+1}. {url}" for idx, url in enumerate(song_queue)])
        await ctx.send(f"Current Queue:\n{queue_list}")
    else:
        await ctx.send("The queue is empty.")

@bot.command()
async def clear(ctx):
    song_queue.clear()
    await ctx.send("The queue has been cleared!")

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Paused the music!")
    else:
        await ctx.send("No song is currently playing.")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Resumed the music!")
    else:
        await ctx.send("The music is not paused.")

bot.run(os.getenv("DISCORD_TOKEN"))
