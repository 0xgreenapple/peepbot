from __future__ import annotations
import discord
from discord.ext import commands
from typing import Optional, Literal, TYPE_CHECKING

from handler.pagination import SimpleEmbedPages, EmbedFormatter
from handler.utils import Emojis
if TYPE_CHECKING:
    from pepebot import PepeBot
    from handler.context import Context


class LeaderboardEmbeds(EmbedFormatter):
    def __init__(self, name: str):
        super().__init__(name)

    @staticmethod
    def formate_lines(current_index: int, value) -> str:
        return f"**{current_index}:** {value['user']} ``likes``: {value['likes']} {Emojis.like}"


class MemeCommands(commands.Cog):
    def __init__(self, bot: PepeBot):
        self.bot = bot

    @commands.command(name="meme_lb")
    async def meme_leaderboard(self,ctx: Context):
        like_data = await self.bot.database.select(
            ctx.guild.id,
            table_name="peep.user_details",
            conditions="guild_id = $1",
            columns="user_id,likes",
            filter_by="ORDER BY points DESC "
                      "fetch first 500 rows only",
            return_all_rows=True
        )
        formatted_data = []
        for user_data in like_data:
            if user_data["likes"] == 0:
                continue
            data = {
                "user": self.bot.get_user(user_data["user_id"]),
                "likes": user_data["likes"]
            }
            formatted_data.append(data)
        if formatted_data is None or len(formatted_data ) == 0:
            await ctx.error_embed(
                description="meme leaderboard for this guild is not available")
            return

        embed = SimpleEmbedPages(
            bot=self.bot,
            max_per_page=10,
            formatter=LeaderboardEmbeds("**meme leaderboard**"),
            data=formatted_data,
            ctx=ctx,
        )
        await embed.send()

    @commands.command(name='stats')
    @commands.guild_only()
    async def stats(self, ctx: Context, member: discord.Member = None):
        user = member if member else ctx.author

        user_stats = await self.bot.database.select(
            ctx.guild.id,
            table_name="peep.user_details",
            columns="user_id,likes",
            conditions="guild_id=$1",
            filter_by= "order by likes desc"
                       " fetch first 500 rows only",
            return_all_rows=True
        )

        stats = await self.bot.database.select(
            user.id,
            ctx.guild.id,
            table_name="peep.user_details",
            columns="user_id,likes",
            conditions="user_id=$1 AND guild_id=$2",
            return_row=True
        )

        if stats is None or stats == 0:
            if not member:
                embed = discord.Embed(
                    description=f'{self.bot.right}'
                                f' Stats for you are not available at the moment!')
            else:
                embed = discord.Embed(
                    description=f'{self.bot.right}'
                                f' the stats for this user is not available!')
            await ctx.send(embed=embed)
            return

        j = 1
        index = None
        likes = None

        for i in user_stats:
            if stats['user_id'] == i['user_id']:
                index = j
                likes = i['likes']
                break
            j += 1

        top_rank = None
        if index is not None:
            percent = index / len(user_stats)
            if percent <= 0.1:
                top_rank = '1%'
            elif 0.1 <= percent <= 0.25:
                top_rank = '10%'
            elif 0.25 <= percent <= 0.50:
                top_rank = '25%'
            elif 0.50 <= percent <= 0.75:
                top_rank = '75%'
            else:
                top_rank = None

        if top_rank:
            if not member:
                user_stats = f'**rank**: #{index} \n you are top {top_rank} in the list'
            else:
                user_stats = f'**rank**: #{index} \n  {user.name} top {top_rank} in the list'

        else:
            user_stats = f'**rank**: #{index}'

        embed = discord.Embed(
            title=f'``{user.name}`` stats',
            description=f'>>> {self.bot.right} **User**:{user.mention} \n'
                        f'**upvotes**:{likes}'
                        f'\n{user_stats} '
        )

        await ctx.send(embed=embed)


async def setup(bot: PepeBot) -> None:
    await bot.add_cog(MemeCommands(bot))
