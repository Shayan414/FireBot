import discord
from discord.ext import commands
from discord.ext import tasks
import yt_dlp
import asyncio
import datetime
import sys
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Operating hours
START_HOUR = 15   # 3 PM
END_HOUR = 3    # 3 AM

def is_within_hours():
    """Check if the current time is within the bot's operating hours."""
    now = datetime.datetime.now()
    return START_HOUR <= now.hour < END_HOUR

@tasks.loop(minutes=1)
async def check_time():
    """Periodically check if it's outside operating hours and stop the bot."""
    if not is_within_hours():
        print("Outside operating hours. Shutting down...")
        await bot.close()
        sys.exit()

@bot.event
async def on_ready():
    print(f"{bot.user} has connected!")
    if not is_within_hours():
        print("Started outside operating hours. Shutting down...")
        await bot.close()
        sys.exit()
    check_time.start()

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# Queue to manage songs (URL, Title)
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

    # Fetch song information (title and URL)
    if "youtube.com" in search_query or "youtu.be" in search_query:
        song_info = get_song_info(search_query)
    else:
        await ctx.send(f"Searching for: {search_query}")
        song_info = search_youtube(search_query)

    if not song_info:
        await ctx.send("Could not find the song.")
        return

    song_title = song_info['title']
    song_url = song_info['url']

    if not voice_client.is_playing():
        await ctx.send(f"Playing: **{song_title}**")
        play_music(voice_client, song_url)
    else:
        song_queue.append((song_url, song_title))
        await ctx.send(f"Added to queue: **{song_title}**")

def search_youtube(query):
    """Search YouTube and return the first video's title and URL."""
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
            return {'title': first_result.get('title', 'Unknown Title'), 'url': first_result['url']}
    return None

def get_song_info(url):
    """Get song title and audio URL from a direct YouTube URL."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {'title': info.get('title', 'Unknown Title'), 'url': info['url']}
        except Exception as e:
            print(f"Error fetching song info: {e}")
            return None

def play_music(voice_client, song_url):
    """Play audio with FFmpeg."""
    source = discord.FFmpegPCMAudio(song_url)
    voice_client.play(source, after=lambda e: check_queue(voice_client))

def check_queue(voice_client):
    """Check and play the next song in the queue."""
    if song_queue:
        next_song = song_queue.pop(0)
        song_url, song_title = next_song
        play_music(voice_client, song_url)
        asyncio.run_coroutine_threadsafe(
            voice_client.channel.send(f"Now playing: **{song_title}**"), bot.loop
        )

@bot.command()
async def skip(ctx):
    """Skips the current song."""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped!")
    else:
        await ctx.send("No song is currently playing.")

@bot.command()
async def pause(ctx):
    """Pauses the currently playing song."""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Paused the music!")
    else:
        await ctx.send("No song is currently playing.")

@bot.command()
async def resume(ctx):
    """Resumes the paused song."""
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Resumed the music!")
    else:
        await ctx.send("The music is not paused.")

@bot.command()
async def queue(ctx):
    """Displays the current song queue."""
    if song_queue:
        queue_list = "\n".join([f"{i+1}. {title}" for i, (_, title) in enumerate(song_queue)])
        await ctx.send(f"**Current Queue:**\n{queue_list}")
    else:
        await ctx.send("The song queue is empty.")

@bot.command()
async def clear(ctx):
    """Clears the entire song queue."""
    global song_queue
    song_queue = []
    await ctx.send("Cleared the song queue!")

@bot.command()
async def stop(ctx):
    """Stops playback and clears the queue."""
    if ctx.voice_client:
        ctx.voice_client.stop()
        global song_queue
        song_queue = []
        await ctx.send("Stopped playback and cleared the queue!")
    else:
        await ctx.send("I'm not playing any music right now.")

bot.run(os.getenv("DISCORD_TOKEN"))
