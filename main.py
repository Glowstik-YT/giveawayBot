import nextcord
from nextcord.ext import commands, tasks
from nextcord.abc import GuildChannel
from nextcord import Interaction, ChannelType
from config import TOKEN, PREFIX, OWNER
import os
import aiosqlite

intents = nextcord.Intents().all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, case_insensitive=True, allowed_mentions=nextcord.AllowedMentions(
        users=True,
        everyone=False,
        roles=False,
        replied_user=True,
    )
)

for fn in os.listdir("./cogs"):
    if fn.endswith(".py"):
        bot.load_extension(f"cogs.{fn[:-3]}")

@bot.event
async def on_ready():
    print(f"Bot ID: {bot.user.id}\nBot Name: {bot.user.name}")
    setattr(bot, "db", await aiosqlite.connect("main.db"))

@bot.command()
@commands.is_owner()
async def load(ctx, extension):
    try:
        bot.load_extension(f"cogs.{extension}")
    except commands.ExtensionAlreadyLoaded:
        return await ctx.send("Cog is already loaded")
    except commands.ExtensionNotFound:
        return await ctx.send("Cog is not found")
    await ctx.send("Cog loaded")

@bot.command()
@commands.is_owner()
async def reload(ctx, extension):
    try:
        bot.reload_extension(f"cogs.{extension}")
    except commands.ExtensionNotFound:
        return await ctx.send("Cog is not found")
    await ctx.send("Cog reloaded")

@bot.command()
@commands.is_owner()
async def unload(ctx, extension):
    try:
        bot.unload_extension(f"cogs.{extension}")
    except commands.ExtensionNotFound:
        return await ctx.send("Cog is not found")
    await ctx.send("Cog unloaded")

@bot.command()
@commands.is_owner()
async def check(ctx, cog_name):
    try:
        bot.load_extension(f"cogs.{cog_name}")
    except commands.ExtensionAlreadyLoaded:
        await ctx.send("Cog is loaded")
    except commands.ExtensionNotFound:
        await ctx.send("Cog not found")
    else:
        await ctx.send("Cog is unloaded")
        bot.unload_extension(f"cogs.{cog_name}")

@bot.event
async def on_application_command_error(ctx, error):
        if isinstance(error, commands.NotOwner):
            em = nextcord.Embed(
                title="Owner Only Command",
                description=f"Only the bot owner `{OWNER}` is allowed to run this command.",
            )
            await ctx.send(embed=em, delete_after=20)
            return
        else:
            em = nextcord.Embed(title="Error Occured", description=f"```{error}```")
            await ctx.send(embed=em, delete_after=30)
            return

bot.run(${{TOKEN}}) #replace this with bot.run(TOKEN) if your using another host besides railway
