import os
import re
import discord
from discord.ext import commands
from openai import OpenAI
import openai
import random
from datetime import timedelta
from dotenv import load_dotenv

# Set up environment

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Set up OpenAI API
openai.api_key = OPENAI_API_KEY
client = OpenAI()

# Set up Discord bot with intents

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

bot_data = {
    "character_response_frequency":0.02,
    "message_history":[]
}

async def fetch_gpt4_response(system, messages):
    response = client.chat.completions.create(
         model="gpt-3.5-turbo",
         messages= messages + [{
             "role":"system",
             "content":system
         }],
         temperature=2,
         max_tokens=256,
         top_p=0.5,
         frequency_penalty=0.75,
         presence_penalty=1
    )
    print(response)
    return response.choices[0].message.content

def extract_link(text):
    # Regex pattern to match URLs with 'x.com' or 'twitter.com'
    pattern = r'(https?://(?:www\.)?(x\.com|twitter\.com)/\S+)'
    
    # Find all matches in the text
    links = re.findall(pattern, text)
    
    # Return the first link found or None if no link is found
    return links[0][0] if links else None

# Make the bot announce itself when it first connects to Discord.
@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user:
        return
    else:
        bot_data["message_history"] = bot_data["message_history"][-5:]
        bot_data["message_history"] += [{
            "role":"user",
            # "name":message.author.name,
            "content":message.content
        }]

    # ping
    if message.content.startswith("ping"):
        await message.channel.send("pong")
    
    # replace twitter and x links with fxtwitter (embeds)
    if "twitter.com" in message.content or "x.com" in message.content:
        link = extract_link(message.content)
        # Define the regex pattern to match 'twitter.com' or 'x.com'
        pattern = r'(https?://(?:www\.)?)(twitter\.com|x\.com)'
        # Replace the first occurrence of the pattern with 'fxtwitter.com'
        replaced_link = re.sub(pattern, r'\1fxtwitter.com', link, count=1)
        await message.channel.send(replaced_link)

    thresh = bot_data["character_response_frequency"]

    # find the time of the detected message
    timezone_offset = timedelta(hours=-4)
    timestamp = message.created_at + timezone_offset
    formatted_timestamp = timestamp.strftime('%H:%M:%S')

    chance = random.random()
    respond = chance < thresh or (bot.user.mentioned_in(message) and message.channel.name != "general")
    print(f"{formatted_timestamp} - Message received. roll = {chance}   Response = {respond}")

    if respond:
        directive = """---------------------------------
        You are a Discord Bot that responds to random messages from a random perspective.\n\n
        Determine who you are first, by choosing a real historical figure, a fictional character or 
        a set of adjectives and nouns in the format of `[adjective] [noun]` or `[adjective] and [adjective] [noun]`.\n\n
        Then, respond to the message from that perspective. Format your message as follows without variation:\n
        `[perspective]: [content]`. 
        The content should be explicitly related to the original message, either responding directly, asking a question, 
        or making some kind of joke about it. Keep your response to ONLY 1 or 2 short sentences."""
        response = await fetch_gpt4_response(directive, bot_data["message_history"])
        await message.reply(response)
        print("|-----------------------------------------------------------------------------")
        print(f"|Sent response: {response}")
        print("|-----------------------------------------------------------------------------")

bot.run(DISCORD_TOKEN)
