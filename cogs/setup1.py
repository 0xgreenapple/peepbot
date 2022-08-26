import asyncio
import io
import os
import random
import typing
from io import BytesIO

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

from handler.Context import Context
from handler.pagination import SimplePages
from handler.view import duel_button
from pepebot import pepebot
import logging


class leaderboard(SimplePages):
    def __init__(self, entries: list, *, ctx: Context, per_page: int = 12, title: str = None):
        converted = entries
        print(entries)
        super().__init__(converted, per_page=per_page, ctx=ctx)


class setup_memme(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot

    setup = app_commands.Group(name='setup', description='setup commands for you', guild_only=True,
                               default_permissions=discord.Permissions(manage_guild=True))

    @setup.command(name='help', description='help related to setup command')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    async def setup_help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f'``Setup``',
            description=f'>>> {self.bot.right} **run the following commands** \n'
                        f'``/setup vote <channel>`` : \n setup vote channel for you \n '
                        f'``/setup announcements <channel>`` :\n setup announcement channel for you !\n'
                        f'``/setup vote_time <time_in_minutes>`` : \nset voting time \n'
                        f'``/setup customization_time  <time_in_minutes>``:\n setup customisation time\n'
                        f'``/setup meme  <channel>``:\n setup meme channel to pin messages \n'
                        f'``/setup meme_listener <true_or_false> ``: \ndisable OC meme listener \n'
                        f'``/setup deadchat <true_or_false> ``: \ndisable deadchat  listener \n'
                        f'``/setup deadchat_role <role> ``: \n specify deadchat ping role \n'
                        f'``/setup thread <true_or_false> ``: \n disable thread  listener \n'
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        # enable or disable the whole deadchat system

    @setup.command(name='deadchat', description='enable or disable dead chat command')
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def deadchat_disable(self, interaction: discord.Interaction, type: typing.Literal['true', 'false']):
        await interaction.response.defer(ephemeral=True)
        if type == 'true':
            await self.bot.db.execute(
                """ 
                    INSERT INTO test.utils(guild_id1,active)
                    VALUES($1,$2)
                    ON CONFLICT (guild_id1) DO
                    UPDATE SET active = $2
                """, interaction.guild.id, True
            )
        elif type == 'false':
            await self.bot.db.execute(
                """ 
                    INSERT INTO test.utils(guild_id1,active)
                    VALUES($1,$2)
                    ON CONFLICT (guild_id1) DO
                    UPDATE SET active = $2
                """, interaction.guild.id, False
            )
        embed = discord.Embed(
            title='``deadchat listener``',
            description=f"{self.bot.right} deadchat listener has been updated to ``{type}`` \n"
                        f"to setup role do ``$setup deadchat_role <role>``"
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    ## dead chat commands , and setup
    @setup.command(name='deadchat_role', description='setup dead chat role')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    @app_commands.describe(
        role='deadchat ping role'
    )
    async def deadchat_role(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.execute(
            """ 
                INSERT INTO test.utils(guild_id1,role_id1)
                VALUES($1,$2)
                ON CONFLICT (guild_id1) DO
                UPDATE SET role_id1 = $2
            """, interaction.guild.id, role.id
        )

        embed = discord.Embed(
            title='``deadchat listener``',
            description=f"{self.bot.right} deadchat role has been updated to ``{role.mention}`` \n"
        )

        await interaction.followup.send(embed=embed)

    # enable or disable meme listener
    @setup.command(name='meme_listener', description='enable or disable meme listener')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def disable_meme(self, interaction: discord.Interaction, type: typing.Literal['true', 'false']):
        await interaction.response.defer(ephemeral=True)
        if type == 'true':
            await self.bot.db.execute(
                """ 
                INSERT INTO test.setup(guild_id1,listener)
                VALUES($1,$2)
                ON CONFLICT (guild_id1) DO
                UPDATE SET listener = $2
            """, interaction.guild.id, True
            )
        elif type == 'false':
            await self.bot.db.execute(
                """ 
                    INSERT INTO test.setup(guild_id1,listener)
                    VALUES($1,$2)
                    ON CONFLICT (guild_id1) DO
                    UPDATE SET listener = $2
                """, interaction.guild.id, False
            )
        embed = discord.Embed(
            title='``meme listener``',
            description=f"{self.bot.right} meme listener has been updated to ``{type}`` \n"
                        f"to setup channel do ``/setup meme <channel>``"
        )

        await interaction.followup.send(embed=embed)

    # setup voting channel deprecated
    @setup.command(name='vote', description='setup vote channel')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def vote_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,vote)
            VALUES($1,$2) 
            ON CONFLICT (guild_id1) DO
            UPDATE SET vote = $2 ;
            """, interaction.guild.id, channel.id
        )
        embed = discord.Embed(
            title='``vote channel``',
            description=f"{self.bot.right} vote channel has been successfully updated to {channel.mention}"
        )
        await interaction.followup.send(embed=embed)

    # setup voting time for the memes
    @setup.command(name='vote_time', description='setup voting time for the memes')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def vote_time(self, interaction: discord.Interaction, voting_time: int):
        if voting_time > 60:
            embed = discord.Embed(description=f'{self.bot.right} the time must be under 1 hours')
            await interaction.response.send_message(embed=embed, epehemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,vote_time)
            VALUES($1,$2)
            ON CONFLICT (guild_id1) DO
            UPDATE SET vote_time = $2 ;
            """, interaction.guild.id, voting_time
        )

        embed = discord.Embed(
            title='``setup``',
            description=f'>>> {self.bot.right} **voting time has been updated to ``{voting_time}`` min**'
        )

        await interaction.followup.send(embed=embed)

    # customization time made for battle command
    @setup.command(name='customisation_time', description='setup customisation time for meme battle')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def customisation_time(self, interaction: discord.Interaction, customisation_time: int):

        if customisation_time > 60:
            embed = discord.Embed(description=f'{self.bot.right} the time must be under 15 min')
            await interaction.response.send_message(embed=embed, epehemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,customization_time)
            VALUES($1,$2)
            ON CONFLICT (guild_id1) DO
            UPDATE SET customization_time = $2 ;
            """, interaction.guild.id, customisation_time
        )

        embed = discord.Embed(
            title='``setup``',
            description=f'>>> {self.bot.right}**customisation time has been updated to ``{customisation_time}`` min**'
        )
        await interaction.followup.send(embed=embed)

    # oc listener channel
    @setup.command(name='oc-channel', description='setup meme channel for OC listener')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def meme(self, interaction: discord.Interaction, mode: typing.Literal['add', 'remove'],
                   channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)

        channels = await self.bot.db.fetchval(
            """ SELECT meme_channel FROM test.channels WHERE guild_id1=$1""",
            interaction.guild.id
        )

        if mode == 'add':
            if channels is not None:
                if channel.id in channels:
                    embed = discord.Embed(description=f'{self.bot.right} the channel is already in the list')
                    await interaction.followup.send(embed=embed)
                    return

        if channels is not None:
            if mode == 'remove':
                if channel.id not in channels:
                    embed = discord.Embed(
                        description=f'{self.bot.right} there is no channel called {channel.mention} in the list')
                    await interaction.followup.send(embed=embed)
                    return

        if channels is None:
            channels = []
            channels.append(channel.id)
        else:
            if mode == 'add':
                channels.append(channel.id)
            else:
                channels.remove(channel.id)

        await self.bot.db.execute(
            """
            INSERT INTO test.channels(guild_id1,meme_channel)
            VALUES($1,$2) 
            ON CONFLICT (guild_id1) DO
            UPDATE SET meme_channel = $2 ;
            """, interaction.guild.id, channels
        )
        embed = discord.Embed(
            title='``OC channel``',
            description=f"{self.bot.right} {channel.mention} {'added' if mode == 'add' else 'removed'} to the list"
        )
        await interaction.followup.send(embed=embed)

    # enable or disable the whole thread system
    @setup.command(name='thread-listener', description='enable or disable thread-listener')
    @app_commands.describe(
        message='the message that bot will send in the thread')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def disable_thread(self, interaction: discord.Interaction, type: typing.Literal['true', 'false'],
                             message: str = None):
        await interaction.response.defer(ephemeral=True)
        if type == 'true':
            await self.bot.db.execute(
                """ 
                INSERT INTO test.setup(guild_id1,thread_ls,thread_message)
                VALUES($1,$2,$3)
                ON CONFLICT (guild_id1) DO
                UPDATE SET thread_ls = $2,thread_message = $3
            """, interaction.guild.id, True, message if message else "make sure the meme is **original**"
            )
        elif type == 'false':
            await self.bot.db.execute(
                """ 
                    INSERT INTO test.setup(guild_id1,thread_ls)
                    VALUES($1,$2)
                    ON CONFLICT (guild_id1) DO
                    UPDATE SET thread_ls = $2
                """, interaction.guild.id, False
            )

        embed = discord.Embed(
            title='``meme listener``',
            description=f"{self.bot.right} thread listener has been updated to ``{type}`` \n"
                        f"to setup channel do ``/setup thread-channel <channel>``"
        )
        await interaction.followup.send(embed=embed)

    # add or remove thread channels from the list
    @setup.command(name='thread-channel', description='setup thread channel for oc listener')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def thread_channel(self, interaction: discord.Interaction, mode: typing.Literal['remove', 'add'],
                             channel: discord.TextChannel, msg: str = None):
        await interaction.response.defer(ephemeral=True)
        channels = await self.bot.db.fetch(
            """SELECT channel_id FROM  test.thread_channel WHERE guild_id = $1""",
            interaction.guild.id
        )
        if mode == 'add':
            for i in channels:
                if i['channel_id'] == channel.id:
                    if msg is None:
                        await interaction.followup.send("channel already in list if you want to remove run "
                                                        "``thread-channel mode:remove``")
                    else:
                        await self.bot.db.execute(
                            """
                            INSERT INTO test.thread_channel(guild_id, channel_id,msg)
                            VALUES($1,$2,$3) 
                            ON CONFLICT (guild_id, channel_id) DO
                            UPDATE SET msg = $3
                            """, interaction.guild.id, channel.id, msg
                        )

                    return

            await self.bot.db.execute(
                """
                INSERT INTO test.thread_channel(guild_id, channel_id,msg)
                VALUES($1,$2,$3) 
                ON CONFLICT (guild_id, channel_id) DO
                UPDATE SET msg = $3
                """, interaction.guild.id, channel.id, msg
            )
            embed = discord.Embed(
                title='``thread channel``',
                description=f"{self.bot.right} thread channel added ``{channel.mention}`` \n"
                            f"message:``none``"
            )
            await interaction.followup.send(
                embed=embed
            )
        elif mode == 'remove':
            for i in channels:
                if i['channel_id'] == channel.id:
                    await self.bot.db.execute(
                        """
                        DELETE FROM test.thread_channel
                        WHERE guild_id = $1 AND channel_id = $2
                        """, interaction.guild.id, channel.id
                    )
                    embed = discord.Embed(
                        title='``thread channel deleted``',
                        description=f"{self.bot.right} thread channel deleted: ``{channel.mention}`` \n"
                    )

                    await interaction.followup.send(
                        embed=embed
                    )
                    return
            await interaction.followup.send("the channel already not in the list try again")

    # setup shop log channel
    @setup.command(name='shop-log', description='setup shop log channel')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def shop_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.execute(
            """
            INSERT INTO test.channels(guild_id1,shop_log)
            VALUES($1,$2) 
            ON CONFLICT (guild_id1) DO
            UPDATE SET shop_log = $2 ;
            """, interaction.guild.id, channel.id
        )
        embed = discord.Embed(
            title='``shop_log channel``',
            description=f"{self.bot.right} shop_log channel has been successfully updated to {channel.mention}"
        )
        await interaction.followup.send(embed=embed)

    # setup reaction channel which bot will react in
    @setup.command(name='meme-channel',
                   description='add a reaction channel where bot will automatically react to memes and move it to '
                               'gallery')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def reaction_channel(self, interaction: discord.Interaction, mode: typing.Literal['remove', 'add'],
                               channel: discord.TextChannel,
                               ):
        await interaction.response.defer(ephemeral=True)

        channels = await self.bot.db.fetchval(
            """ SELECT reaction_channel FROM test.channels WHERE guild_id1=$1""",
            interaction.guild.id
        )

        if mode == 'add':
            if channels is not None:
                if channel.id in channels:
                    embed = discord.Embed(description=f'{self.bot.right} the channel is already in the list')
                    await interaction.followup.send(embed=embed)
                    return

        if channels is not None:
            if mode == 'remove':
                if channel.id not in channels:
                    embed = discord.Embed(
                        description=f'{self.bot.right} there is no channel called {channel.mention} in the list')
                    await interaction.followup.send(embed=embed)
                    return

        if channels is None:
            channels = []
            channels.append(channel.id)
        else:
            if mode == 'add':
                channels.append(channel.id)
            else:
                channels.remove(channel.id)

        await self.bot.db.execute(
            """
            INSERT INTO test.channels(guild_id1,reaction_channel)
            VALUES($1,$2) 
            ON CONFLICT (guild_id1) DO
            UPDATE SET reaction_channel = $2 ;
            """, interaction.guild.id, channels
        )
        embed = discord.Embed(
            title='``reaction channel``',
            description=f"{self.bot.right} {channel.mention} {'added' if mode == 'add' else 'removed'} to the list"
        )
        await interaction.followup.send(embed=embed)

    # enable or disable the whole like system
    @setup.command(name='auto-reactions', description='enable or disable auto reaction system')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def desable_reaction(self, interaction: discord.Interaction, type: typing.Literal['true', 'false']):
        await interaction.response.defer(ephemeral=True)
        if type == 'true':
            await self.bot.db.execute(
                """ 
                INSERT INTO test.setup(guild_id1,reaction_ls)
                VALUES($1,$2)
                ON CONFLICT (guild_id1) DO
                UPDATE SET reaction_ls = $2
            """, interaction.guild.id, True
            )
        elif type == 'false':
            await self.bot.db.execute(
                """ 
                    INSERT INTO test.setup(guild_id1,reaction_ls)
                    VALUES($1,$2)
                    ON CONFLICT (guild_id1) DO
                    UPDATE SET reaction_ls = $2
                """, interaction.guild.id, False
            )
        embed = discord.Embed(
            title='``auto reaction``',
            description=f"{self.bot.right} reaction listener has been updated to ``{type}`` \n"
                        f"to setup channel do ``/setup reaction-channel``"
        )

        await interaction.followup.send(embed=embed)

    # setup likes for each gallery
    @setup.command(name='likes', description='how many likes need to get to the gallery levels channel')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def likes(
            self, interaction: discord.Interaction, channel: discord.TextChannel, like: int
    ):

        await interaction.response.defer(ephemeral=True)

        await self.bot.db.execute(
            """
            INSERT INTO test.likes(guild_id1,channel,likes)
            VALUES($1,$2,$3) 
            ON CONFLICT (guild_id1,channel) DO
            UPDATE SET likes = $3;
            """, interaction.guild.id, channel.id, like
        )

        embed = discord.Embed(
            title='``likes ``',
            description=f"{self.bot.right} **likes for {channel.mention} has been updated to {like} {self.likes}**"
        )
        await interaction.followup.send(embed=embed)

    @setup.command(name='remove-gallery', description='remove a gallery channel from the list')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def gallery_remove(
            self, interaction: discord.Interaction,
            channel: typing.Literal['gallery_lvl1', 'gallery_lvl2', 'gallery_lvl3', 'gallery_lvl4', 'gallery_lvl5',
                                    'gallery_lvl6']
    ):
        await interaction.response.defer(ephemeral=True)

        channels = await self.bot.db.fetch(
            """
            SELECT gallery_l1,gallery_l2,gallery_l3,gallery_l4,gallery_l5,gallery_l6
            FROM test.channels WHERE guild_id1= $1;
            """, interaction.guild.id
        )

        newchannels = [channels[0]['gallery_l1'], channels[0]['gallery_l2'], channels[0]['gallery_l3'],
                       channels[0]['gallery_l4'],
                       channels[0]['gallery_l5'], channels[0]['gallery_l6']]
        newchannels3 = []
        msg = ""

        if channel == 'gallery_lvl1':
            if newchannels[0]:
                for i in range(len(newchannels)):
                    newchannels[i] = None
            else:
                await interaction.followup.send("**the gallery already not exist**")
        elif channel == 'gallery_lvl2':
            if newchannels[1]:
                for i in range(len(newchannels)):
                    if i >= 1:
                        newchannels[i] = None
            else:
                await interaction.followup.send("**the gallery already not exist**")
                return

        elif channel == 'gallery_lvl3':
            if newchannels[2]:
                for i in range(len(newchannels)):
                    if i >= 2:
                        newchannels[i] = None
            else:
                await interaction.followup.send("**the gallery already not exist**")
                return

        elif channel == 'gallery_lvl4':
            if newchannels[3]:
                for i in range(len(newchannels)):
                    if i >= 3:
                        newchannels[i] = None
            else:
                await interaction.followup.send("**the gallery already not exist**")
                return

        elif channel == 'gallery_lvl5':
            if newchannels[4]:
                for i in range(len(newchannels)):
                    if i >= 4:
                        newchannels[i] = None
            else:
                await interaction.followup.send("**the gallery already not exist**")
                return

        elif channel == 'gallery_lvl6':
            if newchannels[5]:
                for i in range(len(newchannels)):
                    if i >= 5:
                        newchannels[i] = None
            else:
                await interaction.followup.send("**the gallery already not exist**")
                return

        for i in newchannels:
            if i:
                cs = interaction.guild.get_channel(int(i))
                newchannels3.append(cs.mention)
        print(newchannels[1])

        await self.bot.db.execute(
            """
            INSERT INTO test.channels(guild_id1,gallery_l1,gallery_l2,gallery_l3,gallery_l4,gallery_l5,gallery_l6)
            VALUES($1,$2,$3,$4,$5,$6,$7) 
            ON CONFLICT (guild_id1) DO
            UPDATE SET gallery_l1 = $2,gallery_l2 = $3,gallery_l3 = $4,
            gallery_l4 = $5,gallery_l5 = $6,gallery_l6 = $7;
            """, interaction.guild.id, newchannels[0], newchannels[1], newchannels[2], newchannels[3], newchannels[4],
            newchannels[5])

        if not newchannels3:
            await interaction.followup.send("all gallery channels has been removed")
            return
        embed_msg = ' <:doubleright:975326725389037568> '.join(newchannels3)

        embed = discord.Embed(
            title='``gallery ``',
            description=f"{self.bot.right} **gallery channels has been updated** \n"
                        f"{embed_msg}"
        )

        await interaction.followup.send(embed=embed)

    @setup.command(name='gallery', description='setup gallery channels')
    @app_commands.describe(
        gallery_lvl1="first channel where the memes will go after reaching certain likes",
        gallery_lvl2="the second gallery channel where the memes will be posted from first gallery channel after "
                     "reaching certain likes ",
        gallery_lvl3="the third gallery channel where the memes will be posted from second gallery channel after "
                     "reaching certain likes ",
        gallery_lvl4="the forth lvl of gallery channel where the memes will be posted from third gallery channel after "
                     "reaching certain likes ",
        gallery_lvl5="the fifth gallery channel where the memes will be posted from forth gallery channel after "
                     "reaching certain likes ",
        gallery_lvl6="the sixth gallery channel where the memes will be posted from fifth gallery channel after "
                     "reaching certain likes "
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def gallery(
            self, interaction: discord.Interaction, gallery_lvl1: discord.TextChannel = None, *,
            gallery_lvl2: discord.TextChannel = None, gallery_lvl3: discord.TextChannel = None,
            gallery_lvl4: discord.TextChannel = None, gallery_lvl5: discord.TextChannel = None,
            gallery_lvl6: discord.TextChannel = None
    ):

        await interaction.response.defer(ephemeral=True)
        if not (gallery_lvl1 or gallery_lvl2 or gallery_lvl3 or gallery_lvl4 or gallery_lvl5 or gallery_lvl6):
            await interaction.followup.send(
                "choose least one channel"
            )
        channels = await self.bot.db.fetch(
            """
            SELECT gallery_l1,gallery_l2,gallery_l3,gallery_l4,gallery_l5,gallery_l6
            FROM test.channels WHERE guild_id1= $1;
            """, interaction.guild.id
        )


        print('channels two', channels)
        if channels:


            newchannels = [channels[0]['gallery_l1'], channels[0]['gallery_l2'], channels[0]['gallery_l3'],
                           channels[0]['gallery_l4'],
                           channels[0]['gallery_l5'], channels[0]['gallery_l6']]

        else:
            newchannels = [None, None, None,
                           None,
                           None, None]
        if gallery_lvl1:
            await self.bot.db.execute(
                """
                INSERT INTO test.channels(guild_id1,gallery_l1)
                VALUES($1,$2) 
                ON CONFLICT (guild_id1) DO
                UPDATE SET gallery_l1 = $2;
                """, interaction.guild.id, gallery_lvl1.id
            )
        if gallery_lvl2:
            if not newchannels[0] and not gallery_lvl1:
                await interaction.followup.send("It is not possible to set up gallery level2 if you have not set up "
                                                "gallery level1")
                return

            await self.bot.db.execute(
                """
                INSERT INTO test.channels(guild_id1,gallery_l2)
                VALUES($1,$2) 
                ON CONFLICT (guild_id1) DO
                UPDATE SET gallery_l2 = $2;
                """, interaction.guild.id, gallery_lvl2.id
            )
        if gallery_lvl3:
            if not newchannels[1] and not gallery_lvl2:
                await interaction.followup.send("It is not possible to set up gallery level3 if you have not set up "
                                                "gallery level2")
                return
            await self.bot.db.execute(
                """
                INSERT INTO test.channels(guild_id1,gallery_l3)
                VALUES($1,$2) 
                ON CONFLICT (guild_id1) DO
                UPDATE SET gallery_l3 = $2;
                """, interaction.guild.id, gallery_lvl3.id
            )
        if gallery_lvl4:
            if not newchannels[2] and not gallery_lvl3:
                await interaction.followup.send("It is not possible to set up gallery level4 if you have not set up "
                                                "gallery level3")
                return
            await self.bot.db.execute(
                """
                INSERT INTO test.channels(guild_id1,gallery_l4)
                VALUES($1,$2) 
                ON CONFLICT (guild_id1) DO
                UPDATE SET gallery_l4 = $2;
                """, interaction.guild.id, gallery_lvl4.id
            )
        if gallery_lvl5:
            if not newchannels[3] and not gallery_lvl4:
                await interaction.followup.send("It is not possible to set up gallery level5 if you have not set up "
                                                "gallery level4")
                return
            await self.bot.db.execute(
                """
                INSERT INTO test.channels(guild_id1,gallery_l5)
                VALUES($1,$2) 
                ON CONFLICT (guild_id1) DO
                UPDATE SET gallery_l1 = $5;
                """, interaction.guild.id, gallery_lvl5.id
            )
        if gallery_lvl6:
            if not newchannels[4] and not gallery_lvl5:
                await interaction.followup.send("It is not possible to set up gallery level6 if you have not set up "
                                                "gallery level5")
                return
            await self.bot.db.execute(
                """
                INSERT INTO test.channels(guild_id1,gallery_l6)
                VALUES($1,$2) 
                ON CONFLICT (guild_id1) DO
                UPDATE SET gallery_l6 = $2;
                """, interaction.guild.id, gallery_lvl6.id
            )

        channels = await self.bot.db.fetch(
            """
            SELECT gallery_l1,gallery_l2,gallery_l3,gallery_l4,gallery_l5,gallery_l6
            FROM test.channels WHERE guild_id1= $1;
            """, interaction.guild.id
        )
        print('channels two', channels)

        newchannels = [channels[0]['gallery_l1'], channels[0]['gallery_l2'], channels[0]['gallery_l3'],
                       channels[0]['gallery_l4'],
                       channels[0]['gallery_l5'], channels[0]['gallery_l6']]

        newchannels3 = []

        for i in newchannels:
            if i is not None:
                cs = interaction.guild.get_channel(int(i))
                newchannels3.append(cs.mention)

        embed_msg = ' <:doubleright:975326725389037568> '.join(newchannels3)

        embed = discord.Embed(
            title='``gallery ``',
            description=f"{self.bot.right} **gallery channels has been updated** \n"
                        f"{embed_msg}"
        )
        await interaction.followup.send(embed=embed)

    @setup.command(name='rewards-system', description='turn on or turn off whole reward system')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def reward_system(self, interaction: discord.Interaction, type: typing.Literal['true', 'false']):
        await interaction.response.defer(ephemeral=True)
        if type == 'true':
            await self.bot.db.execute(
                """ 
                INSERT INTO test.setup(guild_id1,rewards)
                VALUES($1,$2)
                ON CONFLICT (guild_id1) DO
                UPDATE SET rewards = $2
            """, interaction.guild.id, True
            )
        elif type == 'false':
            await self.bot.db.execute(
                """ 
                    INSERT INTO test.setup(guild_id1,rewards)
                    VALUES($1,$2)
                    ON CONFLICT (guild_id1) DO
                    UPDATE SET rewards = $2
                """, interaction.guild.id, False
            )
        embed = discord.Embed(
            title='``auto reaction``',
            description=f"{self.bot.right} reward system has been updated to  ``{type}`` \n"
                        f"to setup channel do ``/setup rewards role``"
        )

        await interaction.followup.send(embed=embed)

    @setup.command(name='reward-roles', description='setup roles for each channel')
    @app_commands.describe(
        limit_1="first messages limit for the channel",
        role_1="the reward role that member will get after reaching the first limit ",
        limit_2="the role for third gallery channel that member will get ",
        role_2="the role for forth gallery channel that member will get ",
        limit_3="the role for fifth gallery channel that member will get ",
        role_3="the role for sixth gallery channel that member will get "
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def reward_roles1(
            self, interaction: discord.Interaction,
            channel: typing.Literal['gallery_l1', 'gallery_l2', 'gallery_l3', 'gallery_l4', 'gallery_l5', 'gallery_l6'],
            limit_1: int = None, *,
            role_1: discord.Role = None, limit_2: int = None,
            role_2: discord.Role = None, limit_3: int = None,
            role_3: discord.Role = None
    ):
        await interaction.response.defer(ephemeral=True)

        if not (limit_1 or limit_2 or limit_3):
            return await interaction.followup.send("**you must specify one limit**")

        channels = await self.bot.db.fetch(
            """
            SELECT gallery_l1,gallery_l2,gallery_l3,gallery_l4,gallery_l5,gallery_l6
            FROM test.channels WHERE guild_id1= $1;
            """, interaction.guild.id
        )

        print('channels two', channels)

        newchannels = [channels[0]['gallery_l1'], channels[0]['gallery_l2'], channels[0]['gallery_l3'],
                       channels[0]['gallery_l4'],
                       channels[0]['gallery_l5'], channels[0]['gallery_l6']]
        channelnew = None

        if channel == 'gallery_l1':
            if newchannels[0]:
                channelnew = newchannels[0]
            else:
                return await interaction.followup.send("**the gallery_lvl1 has been not set pls run the command "
                                                       "``/setup gallery``**")
        elif channel == 'gallery_l2':
            if newchannels[1]:
                channelnew = newchannels[1]
            else:
                return await interaction.followup.send("**the gallery_l2 has been not set pls run the command "
                                                       "``/setup gallery``**")
        elif channel == 'gallery_l3':
            if newchannels[2]:
                channelnew = newchannels[2]
            else:
                return await interaction.followup.send("**the gallery_lvl3 has been not set pls run the command "
                                                       "``/setup gallery``**")
        elif channel == 'gallery_l4':
            if newchannels[3]:
                channelnew = newchannels[3]
            else:
                return await interaction.followup.send("**the gallery_lvl4 has been not set pls run the command "
                                                       "``/setup gallery``**")
        elif channel == 'gallery_l5':
            if newchannels[4]:
                channelnew = newchannels[4]
            else:
                return await interaction.followup.send("**the gallery_lvl5 has been not set pls run the command "
                                                       "``/setup gallery``**")
        elif channel == 'gallery_l6':
            if newchannels[5]:
                channelnew = newchannels[5]
            else:
                return await interaction.followup.send("**the gallery_lvl6 has been not set pls run the command "
                                                       "``/setup gallery``**")

        if limit_1:
            if not role_1:
                return await interaction.followup.send("you have to also setup the reward role_1 that will"
                                                       " member get after reaching the limit")
            if role_2 and role_3:
                if limit_1 > limit_2 or limit_1 > limit_3:
                    return await interaction.followup.send("first limit cant be greater than other limits")

        if limit_2:
            if not role_2:
                return await interaction.followup.send("you have to also setup the reward role_2 that will"
                                                       " member get after reaching the limit")

            if role_1 and role_3:
                if limit_2 > limit_3 or limit_2 < limit_1:
                    return await interaction.followup.send("second limit cant be greater than last limits")
        if limit_3:
            if not role_3:
                return await interaction.followup.send("you have to also setup the reward role_3 that will"
                                                       " member get after reaching the limit")

            if role_2:
                if limit_3 < limit_2:
                    return await interaction.followup.send("last limit cant be lower than previous limits")
        role_1 = role_1.id if role_1 else None
        role_2 = role_2.id if role_2 else None
        role_3 = role_3.id if role_3 else None
        await self.bot.db.execute(
            """
            INSERT INTO test.rewards(guild_id1,channel_id1,limit_1,limit_2,limit_3,role_1,role_2,role_3)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            ON CONFLICT (guild_id1,channel_id1 )DO
            UPDATE SET limit_1 = $3 , limit_2 = $4, limit_3 = $5,role_1=$6,role_2=$7,role_3 = $8
            """, interaction.guild.id, channelnew, limit_1, limit_2, limit_3, role_1, role_2, role_3
        )
        a = await self.bot.db.fetch(
            """
            SELECT * FROM test.rewards 
            WHERE guild_id1=$1 AND channel_id1 = $2
            """, interaction.guild.id, channelnew
        )
        embed = discord.Embed(title='``role reward``',
                              description='**role reward has been set for gallery channels 1 \n'
                                          f'``limit``:{limit_1} ``limit2``:{limit_2} ``limit3``:{limit_3} \n'
                              )
        await interaction.followup.send(embed=embed)


async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        setup_memme(bot))
