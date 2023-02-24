import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

from handler.context import Context
from pepebot import PepeBot



class help(commands.Cog):
    def __init__(self, bot: PepeBot) -> None:
        self.bot = bot

    @commands.command(name='help')
    @commands.cooldown(1, 5, BucketType.member)
    async def help(self, ctx: Context):
        customization_time = await self.bot.db.fetchval(
            """
            SELECT customization_time from test.setup WHERE guild_id1 =$1
            """, ctx.guild.id
        )
        vote_time = await self.bot.db.fetchval(
            """
            SELECT vote_time from test.setup WHERE guild_id1 =$1
            """, ctx.guild.id
        )
        vote = await self.bot.db.fetchval(
            """
            SELECT vote from test.setup WHERE guild_id1 =$1
            """, ctx.guild.id
        )
        announcment = await self.bot.db.fetchval(
            """SELECT announcement FROM test.setup WHERE guild_id1 = $1""",
            ctx.guild.id
        )
        if vote:
            vote1 = self.bot.get_channel(vote)
        else:
            vote1 = None
        if announcment:
            announcment1 = self.bot.get_channel(announcment)
        else:
            announcment1 = None
        embed = discord.Embed(
            title='``help``',
            description='** a special meme bot made for memesaurus server**')
        embed.add_field(name='Commands:', value=
        "<:right:975326725158346774> ``$battle <user>`` \n"
        "> meme "
        "battle with someone ! You will be given a random meme"
        " template and a separate room to customize it, after "
        "you finish customizing your meme, it will be posted "
        f"in the vote {vote1.mention if vote else ''} channel and the person with the highest "
        f"vote will be announced in the announcement {announcment1.mention if announcment1 else ''}channel. \n "
        f"> ** max time to customise:** {customization_time if customization_time else '10'}m \n"
        f"> **max time to vote:**{vote_time if vote_time else '20'}m \n \n"
        "<:right:975326725158346774> ``$stats <optional user>`` \n"
        "> see your or a user stats and rank on the leaderboard \n \n"
        "<:right:975326725158346774> ``$meme_lb``  \n"
        "> see the leaderboard sorted by top members \n \n"
        "<:right:975326725158346774> ``$template`` \n"
        "> get a random meme template"
        "<:right:975326725158346774> ``$leaderboard`` \n"
        "> see the leaderboard sorted by points"
        "<:right:975326725158346774> ``$bal`` \n"
        "> see how mnay points you or a user have"
        )

        # embed.set_thumbnail(url=self.bot.user.avatar.url)
        await ctx.send(embed=embed)


async def setup(bot: PepeBot) -> None:
    await bot.add_cog(
        help(bot))
