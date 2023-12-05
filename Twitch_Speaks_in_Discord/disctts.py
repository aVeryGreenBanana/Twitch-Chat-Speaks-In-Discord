# Original Written by DougDoug and DDarknut
# Current iteration written by aVeryGreenBanana

# Hello! This file contains the main logic to process Twitch chat and convert it to inputs we can use
# The code is written in Python 3.X
# There are 2 other files needed to run this code:
    # TwitchPlays_KeyCodes.py contains the key codes and functions to press keys in-game. You should not modify this file.
    # TwitchPlays_Connection.py is the code that actually connects to Twitch. You should not modify this file.

# The source code primarily comes from:
    # Wituz's "Twitch Plays" tutorial: http://www.wituz.com/make-your-own-twitch-plays-stream.html
    # PythonProgramming's "Python Plays GTA V" tutorial: https://pythonprogramming.net/direct-input-game-python-plays-gta-v/
    # DDarknut's message queue and updates to the Twitch networking code

# Disclaimer: 
    # This code is NOT intended to be professionally optimized or organized.
    # We created a simple version that works well for livestreaming, and I'm sharing it for educational purposes.

##########################################################

TWITCH_CHANNEL = 'averygreenbanana' # Replace this with your Twitch username. Must be all lowercase. 

##########################################################
from discord.ext import commands
import discord
import TwitchPlays_Connection
import pyautogui
#import random
import time
#import pydirectinput
import keyboard
from collections import Counter
import concurrent.futures
from TwitchPlays_KeyCodes import *
from pynput.keyboard import Key, Controller

MESSAGE_RATE = 0.5
MAX_QUEUE_LENGTH = 50  
MAX_WORKERS = 100 # Maximum number of threads you can process at a time 

BOT_TOKEN = '' # Place your bot token between the quotation marks. DONT SHARE YOUR BOT TOKEN WITH ANYONE
CHANNEL_ID =  # Place your channel ID next to the equals, no need for quotations

bot = commands.Bot(command_prefix= "!", intents =discord.Intents.all())

#general variables
pauseTime = 10.0; # amount of cooldown time between tts triggers (in seconds)
cooldownCount = 5 # every 5 messages is when the tts command will activate. Change this to 1 for no cooldown
ttsAttempts = 0

#boolean variables (true or false stuff)
isTalking = False;

last_time = time.time()
message_queue = []
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
active_tasks = []
pyautogui.FAILSAFE = False

##########################################################

# An optional count down before starting, so you have time to load up the game
countdown = 3
while countdown > 0:
    print(countdown)
    countdown -= 1
    time.sleep(1)

t = TwitchPlays_Connection.Twitch();
t.twitch_connect(TWITCH_CHANNEL);

async def callMessages(active_tasks, message_queue, last_time):
    global ttsAttempts
    while True:
        active_tasks = [t for t in active_tasks if not t.done()]
        #Check for new messages
        new_messages = t.twitch_receive_messages();
        #print(f'New msg ({new_messages}) ')
        if new_messages:
            message_queue += new_messages; # New messages are added to the back of the queue
            message_queue = message_queue[-MAX_QUEUE_LENGTH:] # Shorten the queue to only the most recent X messages

        messages_to_handle = []
        if not message_queue:
            # No messages in the queue
            last_time = time.time()
        else:
            # Determine how many messages we should handle now
            r = 1 if MESSAGE_RATE == 0 else (time.time() - last_time) / MESSAGE_RATE
            n = int(r * len(message_queue))
            if n > 0:
                # Pop the messages we want off the front of the queue
                messages_to_handle = message_queue[0:n]
                del message_queue[0:n]
                last_time = time.time();

        # If user presses Shift+Backspace, automatically end the program
        if keyboard.is_pressed('shift+backspace'):
            exit()

        if not messages_to_handle:
            continue
        else:
            for message in messages_to_handle:
                if len(active_tasks) <= MAX_WORKERS:
                    channel = bot.get_channel(CHANNEL_ID)
                    msg = message['message'].lower()
                    #username = message['username'].lower()
                    #print(msg)
                    #print(username)
                    if "+tts" in msg:
                        ttsAttempts += 1
                        if ttsAttempts % cooldownCount == 1 or cooldownCount == 1:
                            theMessage = msg.split(' ', 1)[1]
                            messageIt = str(theMessage)
                            await channel.send(messageIt, tts=True) 
                else:
                    print(f'WARNING: active tasks ({len(active_tasks)}) exceeds number of workers ({MAX_WORKERS}). ({len(message_queue)} messages in the queue)')

@bot.event
async def on_ready():
    bot.loop.create_task(callMessages(active_tasks, message_queue,last_time))

bot.run(BOT_TOKEN)