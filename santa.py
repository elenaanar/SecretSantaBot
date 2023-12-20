import os
import discord
from discord import app_commands
from dotenv import load_dotenv
import json
import random

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.members = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

def load_data(guild_id):
    filename = f'hats_{guild_id}.json'
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"hats": {}}

def save_data(data, guild_id):
    filename = f'hats_{guild_id}.json'
    with open(filename, 'w') as file:
        json.dump(data, file)


@tree.command(name="hats", description="List all available Secret Santa hats.")
async def list_hats(ctx):
    """List all available Secret Santa hats."""

    data = load_data(ctx.guild_id)

    if not data["hats"]:
        await ctx.response.send_message("There are no Secret Santa hats available.")
        return

    hat_list = "\n".join(f"- {hat}" for hat in data["hats"].keys())
    await ctx.response.send_message(f"Available Secret Santa hats:\n{hat_list}")

@tree.command(name="join", description="Join a Secret Santa hat!")
async def join_hat(ctx, hat_name: str = "New Hat"):
    """Join a Secret Santa hat."""

    data = load_data(ctx.guild_id)

    if hat_name not in data["hats"]: # creating a hat if need be
        data["hats"][hat_name] = []
    
    hat_data = data["hats"].get(hat_name, []) # getting the pairs from the input hat

    if len(hat_data)  > 0 and -1 not in [p["drawn"] for p in hat_data]: #if all the users have been drawn 
        await ctx.response.send_message(f'{ctx.user.name} you cannot join the **{hat_name}** hat, it\'s all full! You can make a new hat with /join')
        return
    
    if ctx.user.id not in [pair["participant"] for pair in data["hats"][hat_name]]:
        data["hats"][hat_name].append({"participant": ctx.user.id, "drawn": -1})
        save_data(data, ctx.guild_id)
        await ctx.response.send_message(f'{ctx.user.name} joined the **{hat_name}** Secret Santa hat!')
    else:
        await ctx.response.send_message(f'{ctx.user.name}, you are already in the **{hat_name}** hat.')

@tree.command(name="draw", description="Draw a Secret Santa name.")
async def draw_name(ctx, hat_name: str = "New Hat"):
    """Draw a Secret Santa name."""
    
    data = load_data(ctx.guild_id)

    if hat_name not in data["hats"]:
        await ctx.response.send_message(f'There is no **{hat_name}**! Use /join to add one!')
        return
    if len(data["hats"][hat_name]) < 2:
        await ctx.response.send_message(f'Not enough participants in the **{hat_name}** hat to draw names.')
        return

    user_id = ctx.user.id
    drawn_pair = next((pair for pair in data["hats"][hat_name] if pair["participant"] == user_id), None)

    if drawn_pair is None or drawn_pair["drawn"] == -1:
        hat_data = data["hats"].get(hat_name, []) # getting the pairs from the input hat
    
        available_participants = [pair["participant"] for pair in hat_data if pair["participant"] != user_id and pair["participant"] not in [p["drawn"] for p in hat_data]]
        if not available_participants:
            await ctx.response.send_message(f'{ctx.user.name}, you have already drawn all names in the **{hat_name}** hat.')
            return 

        drawn_id = random.choice(available_participants) if available_participants else None

        drawn_pair["drawn"] = drawn_id
        save_data(data, ctx.guild_id)

        await ctx.response.send_message(f'{ctx.user.name}, you drew {bot.get_user(drawn_id).name} in the **{hat_name}** hat!', ephemeral=True)
    else:
        drawn_name = bot.get_user(drawn_pair["drawn"]).name
        await ctx.response.send_message(f'{ctx.user.name}, you have already drawn {drawn_name} in the **{hat_name}** hat.', ephemeral=True)

@tree.command(name="delete", description="Delete a Secret Santa hat.")
async def delete_hat(ctx, hat_name: str):
    """Delete a Secret Santa hat."""
    
    data = load_data(ctx.guild_id)

    if hat_name in data["hats"]:
        del data["hats"][hat_name]
        save_data(data, ctx.guild_id)
        await ctx.response.send_message(f'The **{hat_name}** hat has been deleted.')
    else:
        await ctx.response.send_message(f'The **{hat_name}** hat does not exist.')

@tree.command(name="help", description="A list of the commands.")
async def help(ctx):
    """A list of the commands."""
    await ctx.response.send_message(f'/join: use to make a new hat or join an existing one (include name of hat).\n/hats: see a list of all the current hats.\n/delete: delete a hat.\n/draw: draw a name from a hat (include name of hat).\n')
    # await ctx.response.send_message(f'/hats: see a list of all the current hats.\n')
    # await ctx.response.send_message(f'/delete: delete a hat.\n')
    # await ctx.response.send_message(f'/draw: draw a name from a hat (include name of hat).\n')


@bot.event
async def on_ready():
    print("The Secret Santa Bot is Online!")
    await tree.sync()

bot.run(TOKEN)

#thigns to fix
# ✅ edge case: someone can't join hat unless there is at least one person who hasnt drawn
# add multiple guilds
# embeds