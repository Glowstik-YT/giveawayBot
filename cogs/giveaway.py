import nextcord
from nextcord.ext import commands, tasks, application_checks
from nextcord.abc import GuildChannel
from nextcord import Interaction, ChannelType, SlashOption
import asyncio
import humanfriendly
import time as pyTime
import json, random

class JoinGiveaway(nextcord.ui.View):
    def __init__(self, time, name, guild, epochEnd, bot):
        super().__init__(timeout=time)
        self.name = name
        self.guild = guild
        self.time = epochEnd
        self.bot = bot

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)

    @nextcord.ui.button(label="Join Giveaway", style=nextcord.ButtonStyle.blurple, custom_id="join"
    )
    async def Join(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        async with self.bot.db.cursor() as cursor:
            await cursor.execute("SELECT participants FROM giveaways WHERE guild = ? AND prize = ? AND time = ?", (self.guild, self.name, self.time))
            data = await cursor.fetchone()
            if data:
                participants = data[0]
                try:
                    participants = json.loads(participants)
                except:
                    participants = []
                if interaction.user.id in participants:
                    return await interaction.response.send_message("You have already joined this giveaway", ephemeral=True)
                else:
                    participants.append(interaction.user.id)
                await cursor.execute("UPDATE giveaways SET participants = ? WHERE guild = ? AND prize = ? AND time = ?", (json.dumps(participants), self.guild, self.name, self.time))
                await interaction.response.send_message("Congrats! You have joined the giveaway :D", ephemeral=True)
            else:
                await interaction.response.send_message("This giveaway doesn't seem to exist or it may have already ended...", ephemeral=True)
        await self.bot.db.commit()


class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(seconds=5)
    async def giveawayCheck(self):
        async with self.bot.db.cursor() as cursor:
            await cursor.execute("SELECT time, prize, message, channel, guild, participants, winners, finished FROM giveaways")
            data = await cursor.fetchall()
            if data:
                for table in data:
                    time, prize, message, channel, guild, participants, winners, finished = table[0], table[1], table[2], table[3], table[4], table[5], table[6], table[7]
                    if not finished:
                        if pyTime.time() >= time:
                            guild = self.bot.get_guild(guild)
                            channel = guild.get_channel(channel)
                            if guild or channel is not None:
                                try:
                                    participants = json.loads(table[5])
                                except:
                                    participants = []
                                if not len(participants) == 0:  
                                    if len(participants) < winners:
                                        winner = random.choices(participants, k=len(participants))
                                    else:
                                        winner = random.choices(participants, k=winners)
                                    winners = []
                                    for user in winner:
                                        winners.append(guild.get_member(int(user)).name)
                                    if winner is not None:
                                        em = nextcord.Embed(title="Giveaway Results", description=f"CONGRATS `{', '.join(winners)}` have/has won the giveaway for `{prize}` :tada:")
                                        await channel.send(embed=em)
                                        await cursor.execute("UPDATE giveaways SET finished = ? WHERE guild = ? AND prize = ? AND message = ?", (True, guild.id, prize, message))
                                        msg = await channel.fetch_message(message)
                                        newEm = nextcord.Embed(title="Giveaway Ended", description=f"`{', '.join(winners)}` have/has won `{prize}` :tada: :tada: :tada:", color=nextcord.Color.blurple())
                                        newEm.set_footer(text=f"Participants: {len(participants)}")
                                        await msg.edit(embed=newEm)
                                else:
                                    await cursor.execute("UPDATE giveaways SET finished = ? WHERE guild = ? AND prize = ? AND message = ?", (True, guild.id, prize, message))
                                    msg = await channel.fetch_message(message)
                                    newEm = nextcord.Embed(title=f"{prize} Giveaway Ended", description=f"No one joined this giveaway <:cri:796075215741255691>", color=nextcord.Color.blurple())
                                    await msg.edit(embed=newEm)
                                    em = nextcord.Embed(title=f"{prize} Giveaway Ended", description="No one joined the giveaway :(")
                                    await channel.send(embed=em)
        await self.bot.db.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(2)
        async with self.bot.db.cursor() as cursor:
            await cursor.execute("CREATE TABLE IF NOT EXISTS giveaways (time INTEGER, prize TEXT, message INTEGER, channel INTEGER, guild INTEGER, participants TEXT, winners INTEGER, finished BOOL)")
        await self.bot.db.commit()
        print("Database Staus: Online")
        self.giveawayCheck.start()
        print("Giveaway Loop: Online")

    @nextcord.slash_command(name="ping", description="Check the bots ping")
    async def ping(self, interaction: Interaction):
        em = nextcord.Embed(title="Bots Ping")
        em.add_field(
            name="My API Latency is:", value=f"{round(self.bot.latency*1000)} ms"
        )
        em.set_footer(
            text=f"Ping requested by {interaction.user}", icon_url=interaction.user.display_avatar
        )
        await interaction.response.send_message(embed=em)
    
    @nextcord.slash_command(name="giveaway", description="Giveaway Mast Command [No Function]")
    async def giveaway(self, interaction: Interaction):
        return
    
    @giveaway.subcommand(name="start", description="Start a giveaway")
    @application_checks.has_permissions(manage_messages=True)
    async def start(self, interaction: Interaction, prize: str = SlashOption(description="The prize of the giveaway", required=True), channel: GuildChannel = SlashOption(channel_types=[ChannelType.text], description="What text channel should the giveaway be in?", required=True), time: str = SlashOption(description="The amount of time the giveaway should go on for i.e 5d, 6h, 30m", required=True), winners: int = SlashOption(description="The amount of winners for the giveaway", required=True)):
        time = humanfriendly.parse_timespan(time)
        epochEnd = pyTime.time() + time
        async with self.bot.db.cursor() as cursor:
            await cursor.execute("INSERT INTO giveaways (time, prize, message, channel, guild, participants, winners, finished) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (epochEnd, prize, "", channel.id, interaction.guild.id, "", winners, False)
            )
            embed = nextcord.Embed(title=f"🎉{prize}🎉", description=f"Ends at <t:{int(epochEnd)}:f> or <t:{int(epochEnd)}:R>\nWinner(s): `{winners}`\nClick `Join Giveaway` to join!", color=nextcord.Color.blurple())
            await interaction.response.send_message(f"Giveaway started in {channel.mention}", ephemeral=True)
            view = JoinGiveaway(time, prize, interaction.guild.id, epochEnd, self.bot)
            msg = await channel.send(embed=embed, view=view)
            view.message = msg
            await cursor.execute("UPDATE giveaways SET message = ? WHERE guild = ? AND prize = ? AND time = ?", (msg.id, interaction.guild.id, prize, epochEnd))
        await self.bot.db.commit()
    
    @giveaway.subcommand(name="reroll", description="Reroll the giveaway (picks a new winner)")
    @application_checks.has_permissions(manage_messages=True)
    async def reroll(self, interaction: Interaction, messageid: str = SlashOption(description="The giveaway embed message ID", required=True)):
        try:
            message = int(messageid)
        except ValueError:
            return interaction.response.send_message("You must pass in an integer for the message ID")
        async with self.bot.db.cursor() as cursor:
            await cursor.execute("SELECT participants, channel, prize, winners FROM giveaways WHERE message = ? AND finished = ?", (message, True))
            data = await cursor.fetchone()
            if data:
                try:
                    participants = json.loads(data[0])
                except:
                    participants = []
                if len(participants) == 0:
                    return await interaction.response.send_message("Can not reroll giveaway because no one joined the giveaway")
                if not len(participants) == 0:  
                    if len(participants) < data[3]:
                        winner = random.choices(participants, k=len(participants))
                    else:
                        winner = random.choices(participants, k=data[3])
                    winners = []
                    for user in winner:
                        winners.append(interaction.guild.get_member(int(user)).name)
                channel = interaction.guild.get_channel(data[1])
                if winners and channel is not None:
                    em = nextcord.Embed(title="Giveaway Reroll Results", description=f"CONGRATS `{', '.join(winners)}` have/has won the giveaway for `{data[2]}` :tada:")
                    await channel.send(embed=em)
                    await channel.send(f"CONGRATS {winner.mention} has won the giveaway for `{data[2]}` :tada: [REROLLED]")
                    msg = await channel.fetch_message(data[0])
                    newEm = nextcord.Embed(title="Giveaway Ended", description=f"`{winner}` has won `{data[2]}` :tada: :tada: :tada:", color=nextcord.Color.blurple())
                    newEm.set_footer(text=f"Participants: {len(participants)}")
                    await msg.edit(embed=newEm)
                else:
                    return await interaction.response.send_message("Can not reroll giveaway because the giveaway channel or winner is not found")
            else:
                return await interaction.response.send_message("Can not reroll giveaway because the giveaway does not seem to exist")

def setup(bot):
    bot.add_cog(Giveaway(bot))
