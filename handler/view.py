import argparse
import asyncio
import io
import random
import shlex
from typing import Optional

import aiohttp
import discord
import os

from discord.ui import View
from datetime import datetime, timedelta
import pepebot


class Arguments(argparse.ArgumentParser):
    def error(self, message: str):
        raise RuntimeError(message)


class duel_button(discord.ui.View):
    def __init__(self,
                 message: discord.Message,
                 member: discord.Member,
                 user: discord.Member,
                 bot: pepebot.pepebot
                 ):
        super().__init__(timeout=10 * 60)

        self.message: discord.Message = message
        self.interaction_message = None
        self.member: discord.Member = member
        self.user: discord.Member = user
        self.bot = bot

    @discord.ui.button(label='accept', style=discord.ButtonStyle.blurple)
    async def accept(self, interaction: discord.Interaction, button):

        if interaction.user.id == self.member.id:
            await interaction.response.defer()

            sent_message_url = self.message.jump_url
            embed = discord.Embed(
                title=f'``Duel``',
                description=f'>>> you have 10 min to make best meme from '
                            f'this template, Click the ready button when you are ready! \n'
            )
            session: aiohttp.ClientSession = self.bot.aiohttp_session

            a = await session.request(
                method='GET',
                url='https://api.imgflip.com/get_memes'
            )
            json = await a.json()
            memes = json['botconfig']['memes']
            ids = []

            for i in memes:
                if i['box_count'] == '2' or i['box_count'] == 2:
                    ids.append(i['id'])
            memeid = random.choice(ids)

            for i in memes:
                if i['id'] == f'{memeid}':
                    image = await session.get(url=i['url'])
                    image_byets = await image.read()
                    file = discord.File(fp=io.BytesIO(image_byets), filename='meme.png')
                    view = ready_button(message=self.message, member=self.member, user=self.user,
                                        bot=self.bot, embed=embed, ids=ids, memes=memes)
                    await self.message.edit(
                        content=None,
                        embed=embed,
                        attachments=[file], view=view
                    )
                    break

            self.bot.loop.create_task(self.bot.db.execute(
                """INSERT INTO test.duel(user_id1,user_id2,message_id,meme_id)
                VALUES($1,$2,$3,$4)
                """, self.user.id, self.member.id, self.message.id, memeid
            ))

            view = View()
            url = discord.ui.Button(url=sent_message_url, label='message')
            view.add_item(url)
            if interaction.message.channel.type == discord.ChannelType.private:
                await interaction.message.delete()
                await interaction.followup.send(f'you are ready,lets move!', view=view, ephemeral=True)
        else:

            await interaction.response.send_message('this is not for you', ephemeral=True)

    @discord.ui.button(label='cancel', style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button):
        if interaction.user.id == self.member.id:
            int_message = interaction.message

            await self.message.edit(content=f'{interaction.user.mention} rejected the invite find another participant!',
                                    view=None)
            if interaction.message.channel.type == discord.ChannelType.private:
                await interaction.message.delete()
                await interaction.response.send_message('successfully canceled the match', ephemeral=True)
        else:
            await interaction.response.send_message('this is not for you', ephemeral=True)

    async def on_timeout(self) -> None:
        try:
            embed = discord.Embed(
                title='``timeout``',
                description=f">>> **{self.bot.right} you failed to accept the meme battle invite in time** \n"
                            f"invited by: {self.user.mention}"
            )
            embed1 = discord.Embed(
                title='``timeout``',
                description=f">>> **{self.bot.right} {self.user.mention} failed to accept the meme battle invite in "
                            f"time** "

            )
            await self.interaction_message.edit(embed=embed, view=None)
            await self.message.edit(embed=embed1, content=None)


        except:
            pass

    async def on_error(self, interaction: discord.Interaction, error: Exception, item) -> None:
        if not interaction.response.is_done():
            await interaction.response.send_message('something went wrong', ephemeral=True)
        else:
            await interaction.followup.send('something went wrong', ephemeral=True)


class ready_button(discord.ui.View):
    def __init__(self,
                 message: discord.Message,
                 member: discord.Member,
                 user: discord.Member,
                 bot: pepebot.pepebot,
                 embed: discord.Embed,
                 ids: list,
                 memes: list

                 ):
        super().__init__(timeout=60 * 15)
        self.message: discord.Message = message
        self.member: discord.Member = member
        self.user: discord.Member = user
        self.bot = bot
        self.ids = ids
        self.memes = memes

        self.embed_msg = embed

    async def get_player_img(self, memeid, message2, message3: str = None, *, url):
        res: aiohttp.ClientSession = self.bot.aiohttp_session

        members = []
        first_caption = ''
        secondcaption = ''

        if len(message2) == 2:
            first_caption = ''.join(message2[0])
            secondcaption = ''.join(message2[1])

        elif len(message2) == 1:
            first_caption = ''.join(message2[0])

        password = os.environ.get('IMAGEPASS')
        username = os.environ.get('IMAGEUSER')

        params = {
            'username': f'{username}',
            'password': f'{password}',
            'template_id': f'{memeid}',
            'text0': f'{first_caption.lower()}',
            'text1': f'{secondcaption.lower()}',
        }
        response = await res.request('POST', url, params=params)
        json = await response.json()
        url = json['botconfig']['url']
        image = await res.get(url=url)
        bytes = await image.read()
        file = discord.File(fp=io.BytesIO(bytes), filename='meme.png')
        return file

    async def load_img(self, interaction: discord.Interaction, voting_time: int, customization_time: int):

        # bot session
        session: aiohttp.ClientSession = self.bot.aiohttp_session

        # will use it later
        caption_url = 'https://api.imgflip.com/caption_image'

        # get the list of memes in json formate
        a = await session.request(
            method='GET',
            url='https://api.imgflip.com/get_memes'
        )

        json = await a.json()
        memes = json['botconfig']['memes']
        ids = []

        for i in memes:
            if i['box_count'] == '2' or i['box_count'] == 2:
                ids.append(i['id'])

        memeid = await self.bot.db.fetchval(""" SELECT meme_id FROM test.duel WHERE message_id = $1
        """, self.message.id)
        memeid = memeid

        for i in self.memes:
            if i['id'] == f'{memeid}':
                image = await session.get(url=i['url'])
                image_byets = await image.read()
                break

        thread_one = await self.message.channel.create_thread(
            name=f'{self.member.name} room',
            type=discord.ChannelType.private_thread
            if interaction.guild.premium_tier >= 2
            else discord.ChannelType.public_thread,
            auto_archive_duration=1440
        )

        thread_two = await self.message.channel.create_thread(
            name=f'{self.user.name} room',
            type=discord.ChannelType.private_thread
            if interaction.guild.premium_tier >= 2
            else discord.ChannelType.public_thread,
            auto_archive_duration=1440
        )

        # create dms
        try:
            member_channel = await self.member.create_dm()
            user_channel = await self.user.create_dm()
        except discord.Forbidden or discord.HTTPException:
            await self.message.channel.send('dm is turned off, i cant send invite.. \n aborting the game')
            await self.message.delete()
            return

        view1 = discord.ui.View()
        view2 = discord.ui.View()

        button = discord.ui.Button(label='your room', url=thread_one.jump_url)
        view1.add_item(button)
        button = discord.ui.Button(label='your room', url=thread_two.jump_url)
        view2.add_item(button)

        embed = discord.Embed(title='your room is ready lets move here !')
        await member_channel.send(embed=embed, view=view1)
        await user_channel.send(embed=embed, view=view2)

        sendembed = discord.Embed(
            title="``duel``",
            description='>>> you have 5 min to make best meme from this template \n'
                        'run ``$caption <your first caption>,<your second caption>`` \n'
                        'separate with comma (.) for bottom text'
        )
        password = os.environ.get('IMAGEPASS')
        username = os.environ.get('IMAGEUSER')

        params = {
            'username': f'{username}',
            'password': f'{password}',
            'template_id': f'{memeid}',
            'text0': f'first',
            'text1': f'second',
        }

        res = self.bot.aiohttp_session
        response = await res.request('POST', caption_url, params=params)
        json = await response.json()
        url = json['botconfig']['url']
        image = await res.get(url=url)
        bytes = await image.read()

        file = discord.File(fp=io.BytesIO(bytes), filename='memme.png')

        t_one = await thread_one.send(content=f'{self.member.mention}', file=file, embed=sendembed)

        file = discord.File(fp=io.BytesIO(bytes), filename='memme.png')

        t_two = await thread_two.send(content=f'{self.user.mention}', file=file, embed=sendembed)

        checks = []
        users_msg = []
        users = []
        first_user_submission = []
        second_user_submission = []

        announcement_id = await self.bot.db.fetchval(
            """SELECT announcement FROM test.setup
                WHERE guild_id1 = $1""", interaction.guild.id
        )
        vote_id = await self.bot.db.fetchval(
            """SELECT vote FROM test.setup
                WHERE guild_id1 = $1""", interaction.guild.id
        )
        announcement = self.bot.get_channel(announcement_id) \
            if announcement_id else self.message.channel

        vote = self.bot.get_channel(vote_id) \
            if vote_id else self.message.channel

        def check(message: discord.Message) -> bool:

            if message.author.id == self.member.id and message.content.startswith(
                    '$caption') and message.channel.id == t_one.channel.id:
                failed = True
                spilt = message.content[8:].split(',')
                failed = False
                if not failed:
                    users_msg.append(f"{message.author.mention} has completed")
                    checks.append(message.author.id)
                    users.append({'message': spilt, 'id': message.author.id})
                    self.bot.loop.create_task(t_one.channel.send('submitted'))

            if message.author.id == self.user.id and message.content.startswith(
                    '$caption') and message.channel.id == t_two.channel.id:
                failed = True
                spilt = message.content[8:].split(',')
                failed = False
                if not failed:
                    users_msg.append(f"{message.author.mention} has completed")
                    checks.append(message.author.id)
                    users.append({'message': spilt, 'id': message.author.id})
                    self.bot.loop.create_task(t_two.channel.send('submitted'))

            return len(checks) == 2

        try:
            await self.bot.wait_for(f'message', timeout=customization_time * 60, check=check)
        except asyncio.TimeoutError:
            if len(users) != 0:
                user_id = users[0]['id']
                user = self.message.guild.get_member(user_id)

                first_user_submission = await self.get_player_img(
                    memeid=memeid, message2=users[0]['message'],
                    url=caption_url
                )
                failed_user = self.user if user.id != self.user.id else self.member
                try:
                    await self.message.delete()

                except discord.Forbidden:
                    pass
                await announcement.send(
                    f'by {user.mention} won the duel, {failed_user.mention} failed in time',
                    file=first_user_submission
                )
                try:
                    await thread_one.delete()
                except:
                    pass
                try:
                    await thread_two.delete()
                except:
                    pass

                await self.bot.db.execute(
                    """
                    INSERT INTO test.leaderboard(user_id1,guild_id1,likes)
                    VALUES($1,$2,$3)
                    ON CONFLICT (guild_id1,user_id1) DO
                    UPDATE SET likes = COALESCE(leaderboard.likes, 0) + $3 ;
                    """, failed_user.id, interaction.guild.id, 1
                )

            else:
                try:
                    await self.message.delete()
                except:
                    pass
                try:
                    await thread_one.delete()
                except:
                    pass
                try:
                    await thread_two.delete()
                except:
                    pass
                await self.message.channel.send(
                    f'{self.user.mention} and {self.member.mention} both failed to make meme in {customization_time} min lol',
                    delete_after=60
                )

            return

        if users[0]['id'] == self.user.id:
            print(t_one)
            first_user_submission = await self.get_player_img(
                memeid=memeid, message2=users[0]['message'],
                url=caption_url
            )
        elif users[0]['id'] == self.member.id:
            print(t_two)
            second_user_submission = await self.get_player_img(
                memeid=memeid, message2=users[0]['message'],
                url=caption_url
            )

        if users[1]['id'] == self.user.id:
            first_user_submission = await self.get_player_img(
                memeid=memeid, message2=users[1]['message'],
                url=caption_url
            )

        elif users[1]['id'] == self.member.id:
            print(t_one)
            second_user_submission = await self.get_player_img(
                memeid=memeid, message2=users[1]['message'],
                url=caption_url
            )

        try:
            await self.message.delete()
        except:
            pass

        first_submission = await vote.send(
            f'by {self.user.mention} | vote!',
            file=first_user_submission
        )
        await first_submission.add_reaction("<:pvote:1004443231762776114>")

        second_submission = await vote.send(
            f'by {self.member.mention} | vote!',
            file=second_user_submission

        )
        await second_submission.add_reaction("<:pvote:1004443231762776114>")
        embeed = discord.Embed(title=f'your meme has been submitted in {self.message.channel.name} '
                                     f'deleting channel in 3 sec ...')

        await t_one.edit(embeds=[embeed], attachments=[], view=None)
        await t_two.edit(embeds=[embeed], attachments=[], view=None)
        await asyncio.sleep(3)

        try:
            self.bot.loop.create_task(thread_one.delete())
            self.bot.loop.create_task(thread_two.delete())
        except:
            pass

        sleep_until = datetime.now() + timedelta(seconds=voting_time * 60)
        await discord.utils.sleep_until(sleep_until)

        x_msg = await vote.fetch_message(first_submission.id)
        y_msg = await vote.fetch_message(second_submission.id)

        count1 = 0
        count2 = 0

        for reaction in x_msg.reactions:
            if reaction.emoji.id == 1004443231762776114:
                count1 = reaction.count
                break
        for reaction in y_msg.reactions:
            if reaction.emoji.id == 1004443231762776114:
                count2 = reaction.count
                break

        print(x_msg.reactions)
        print(y_msg.reactions)
        if count1 > count2:
            await first_submission.delete()
            await second_submission.delete()
            if announcement:
                try:
                    await self.message.delete()
                except:
                    print('forbidden')
                first_user_submission = await self.get_player_img(
                    memeid=memeid, message2=users[0]['message'],
                    url=caption_url
                )
                await announcement.send(content=f'{self.user.mention} has won the duel by {count1 - count2} votes!',
                                        file=first_user_submission)
            await self.bot.db.execute(
                """
                INSERT INTO test.leaderboard(user_id1,guild_id1,likes)
                VALUES($1,$2,$3)
                ON CONFLICT (guild_id1,user_id1) DO
                UPDATE SET likes = COALESCE(leaderboard.likes, 0) + $3 ;
                """, self.user.id, interaction.guild.id, count1
            )
        elif count2 > count1:
            await first_submission.delete()
            await second_submission.delete()
            if announcement:
                try:
                    await self.message.delete()
                except:
                    print('forbidden')
                second_user_submission = await self.get_player_img(
                    memeid=memeid, message2=users[0]['message'],
                    url=caption_url
                )
                await announcement.send(content=f'{self.member.mention} has won by {count2 - count1} votes',
                                        file=second_user_submission)
            await self.bot.db.execute(
                """
                INSERT INTO test.leaderboard(user_id1,guild_id1,likes)
                VALUES($1,$2,$3)
                ON CONFLICT (guild_id1,user_id1) DO
                UPDATE SET likes = COALESCE(leaderboard.likes, 0) + $3 ;
                """, self.member.id, interaction.guild.id, count2
            )
        else:
            await first_submission.edit(content=f'{self.member.mention}! no one won that was a draw votes:{count1}')
            await second_submission.edit(content=f'{self.user.mention}! no one won that was a draw votes:{count2}')
            await self.bot.db.execute(
                """
                INSERT INTO test.leaderboard(user_id1,guild_id1,likes)
                VALUES($1,$2,$3)
                ON CONFLICT (guild_id1,user_id1) DO
                UPDATE SET likes = COALESCE(leaderboard.likes, 0) + $3 ;
                """, self.member.id, interaction.guild.id, count1
            )
            await self.bot.db.execute(
                """
                INSERT INTO test.leaderboard(user_id1,guild_id1,likes)
                VALUES($1,$2,$3)
                ON CONFLICT (guild_id1,user_id1) DO
                UPDATE SET likes = COALESCE(leaderboard.likes, 0) + $3 ;
                """, self.user.id, interaction.guild.id, count2
            )

    @discord.ui.button(label='ready', style=discord.ButtonStyle.green)
    async def ready(self, interaction: discord.Interaction, button):
        if interaction.user.id == self.member.id or interaction.user.id == self.user.id:

            await interaction.response.defer()
            is_user_ready = False
            is_member_ready = False
            member1 = await self.bot.db.fetchval(
                """
                SELECT user_ready 
                FROM test.duel WHERE 
                message_id = $1 
                """, self.message.id
            )

            use1r = await self.bot.db.fetchval(
                """
                SELECT member_ready 
                FROM test.duel WHERE 
                message_id = $1 
                """, self.message.id)
            member = self.bot.get_user(self.member.id)
            user = self.bot.get_user(self.user.id)
            desc = self.embed_msg.description
            if interaction.user.id == user.id:
                if not use1r:
                    await self.bot.db.execute(
                        """UPDATE test.duel SET member_ready=$1 WHERE message_id = $2""",
                        True, self.message.id
                    )
                else:
                    await interaction.followup.send('you are already ready', ephemeral=True)

            if interaction.user.id == member.id:
                if not member1:
                    await self.bot.db.execute(
                        """UPDATE test.duel SET user_ready=$1 WHERE message_id = $2""",
                        True, self.message.id
                    )
                else:
                    await interaction.followup.send('you are already ready', ephemeral=True)

            text = []

            member1 = await self.bot.db.fetchval(
                """
                SELECT user_ready 
                FROM test.duel WHERE 
                message_id = $1 
                """, self.message.id
            )

            use1r = await self.bot.db.fetchval(
                """
                SELECT member_ready 
                FROM test.duel WHERE 
                message_id = $1 
                """, self.message.id)

            custimastion_time = await self.bot.db.fetchval(
                """SELECT customization_time FROM test.setup 
                WHERE guild_id1=$1""", interaction.guild.id
            )
            vote_time = await self.bot.db.fetchval(
                """SELECT vote_time FROM test.setup 
                WHERE guild_id1=$1""", interaction.guild.id
            )
            if custimastion_time is None:
                custimastion_time = 5

            if vote_time is None:
                vote_time = 20

            if member1:
                text.append(f"{member.mention} is ready")
            if use1r:
                text.append(f"{user.mention} is ready")

            if len(text) == 2:
                text1 = '\n'.join(text)

                embed = discord.Embed(title='``duel``',
                                      description=f'>>> you have {custimastion_time} min to make best meme **check '
                                                  f'your dms**')
                await self.message.edit(embed=embed, view=None)
                await self.load_img(interaction, customization_time=custimastion_time, voting_time=vote_time)

            else:
                text1 = '\n'.join(text)
                embed = discord.Embed(title='``duel``',
                                      description=f'>>> you have {custimastion_time} min to make best meme from '
                                                  f'this template, Click the ready button when you are ready! \n{text1}')

                await self.message.edit(embed=embed)
        else:
            await interaction.response.send_message(f'this is not for you!', ephemeral=True)

    @discord.ui.button(label='refresh', style=discord.ButtonStyle.green, custom_id='refresh')
    async def refresh(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        session = self.bot.aiohttp_session
        memeid = random.choice(self.ids)
        user_refresh = await self.bot.db.fetchval("""SELECT r_user_ready FROM test.duel WHERE message_id = $1""",
                                                  self.message.id)
        member_refresh = await self.bot.db.fetchval("""SELECT r_member_ready FROM test.duel WHERE message_id = $1""",
                                                    self.message.id)
        member1 = await self.bot.db.fetchval(
            """
            SELECT user_ready 
            FROM test.duel WHERE 
            message_id = $1 
            """, self.message.id
        )
        use1r = await self.bot.db.fetchval(
            """
            SELECT member_ready 
            FROM test.duel WHERE 
            message_id = $1 
            """, self.message.id
        )

        if interaction.user.id == self.member.id:

            if not member1 or member_refresh or not user_refresh:
                self.bot.loop.create_task(
                    self.bot.db.execute("""UPDATE test.duel SET r_user_ready = $1 WHERE message_id = $2""",
                                        True, self.message.id)
                )
                await interaction.followup.send('the other user must also have to refresh to work', ephemeral=True)
                message = await interaction.channel.fetch_message(self.message.id)
                embed = message.embeds[0]
                embed.description = f"{embed.description} \n {interaction.user.mention} requested for refresh"
                await self.message.edit(embed=embed)
            else:
                await interaction.followup.send('you cant refresh any more', ephemeral=True)

        if interaction.user.id == self.user.id:

            if not use1r or user_refresh or not member_refresh:
                self.bot.loop.create_task(
                    self.bot.db.execute("""UPDATE test.duel SET r_member_ready = $1 WHERE message_id = $2""",
                                        True, self.message.id)
                )
                await interaction.followup.send('the other user must also have to refresh to work', ephemeral=True)
                message = await interaction.channel.fetch_message(self.message.id)
                embed = message.embeds[0]
                embed.description = f"{embed.description} \n {interaction.user.mention} requested for refresh"
                await self.message.edit(embed=embed)
            else:
                await interaction.followup.send('you cant refresh any more', ephemeral=True)

        user_refresh = await self.bot.db.fetchval("""SELECT r_user_ready FROM test.duel WHERE message_id = $1""",
                                                  self.message.id)
        member_refresh = await self.bot.db.fetchval("""SELECT r_member_ready FROM test.duel WHERE message_id = $1""",
                                                    self.message.id)
        if member_refresh and user_refresh:
            for i in self.memes:
                if i['id'] == f'{memeid}':
                    image = await session.get(url=i['url'])
                    image_byets = await image.read()
                    view = self
                    item = discord.utils.get(self.children, custom_id="refresh")
                    view.remove_item(item)

                    file = discord.File(fp=io.BytesIO(image_byets), filename='memme.png')
                    message1 = await self.message.edit(
                        attachments=[file], view=view
                    )
                    custimastion_time = await self.bot.db.fetchval(
                        """SELECT customization_time FROM test.setup 
                        WHERE guild_id1=$1""", interaction.guild.id
                    )
                    vote_time = await self.bot.db.fetchval(
                        """SELECT vote_time FROM test.setup 
                        WHERE guild_id1=$1""", interaction.guild.id
                    )
                    self.bot.loop.create_task(self.bot.db.execute(
                        """UPDATE test.duel SET meme_id = $1 WHERE message_id = $2

                        """, memeid, self.message.id
                    ))
                    embed = discord.Embed(title='``duel``',
                                          description=f'>>> you have {custimastion_time} min to make best meme from '
                                                      f'this template, Click the ready button when you are ready!')
                    break

    async def on_timeout(self) -> None:
        try:
            await self.message.delete()
        except:
            print('yes')
        else:
            await self.message.channel.send(f'aborting the battle {self.user.mention} {self.member.mention}')

    async def on_error(self, interaction: discord.Interaction, error: Exception, item) -> None:
        if not interaction.response.is_done():
            await interaction.response.send_message('something went wrong', ephemeral=True)
        else:
            await interaction.followup.send('something went wrong', ephemeral=True)


class interaction_delete_view(discord.ui.View):
    def __init__(
            self,
            ctx: discord.Interaction,

    ):
        super().__init__(timeout=180)
        self.ctx: discord.Interaction = ctx
        self.message: Optional[discord.Message] = None

    @discord.ui.button(label='delete', style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button):
        if interaction.channel.type == discord.ChannelType.private:
            await interaction.message.delete()
        else:
            if interaction.user.id == self.ctx.user.id or interaction.user.id == self.ctx.guild.owner.id:
                await interaction.message.delete()
                return
            else:
                await interaction.response.send_message('this is not for you lol', ephemeral=True)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
            try:
                if self.message:
                    await self.message.edit(view=self)
            except discord.NotFound:
                pass


class interaction_error_button(discord.ui.View):
    def __init__(
            self,
            ctx: discord.Interaction,

    ):
        super().__init__(timeout=180)
        self.message: Optional[discord.Message] = None
        self.ctx: discord.Interaction = ctx

    @discord.ui.button(label='help', style=discord.ButtonStyle.green)
    async def help(self, interaction: discord.Interaction, button):
        if interaction.user.id == self.ctx.user.id or interaction.user.id == self.ctx.guild.owner.id:
            await interaction.response.send_message("no help?")
            return
        else:
            await interaction.response.send_message('this is not for you lol', ephemeral=True)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass


class accept_bought(discord.ui.View):
    def __init__(
            self,
            bot: pepebot.pepebot,
            item: str,
            user: discord.Member

    ):
        super().__init__(timeout=None)
        self.bot = bot
        self.item_name = item
        self.user_id = user

    @discord.ui.button(label='accept', style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button):
        if interaction.user.id == interaction.guild.owner.id or interaction.user.id == 888058231094665266:
            await interaction.response.defer(ephemeral=True)
            await self.bot.db.execute('DELETE FROM test.inv WHERE user_id = $1 AND guild_id=$2 AND items = $3 ',
                                      self.user_id.id, self.user_id.guild.id, self.item_name)

            await interaction.delete_original_message()
            await interaction.followup.send('done')

            return
        else:
            await interaction.response.send_message('only owner can do it', ephemeral=True)

    @discord.ui.button(label='cancel', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button):
        if interaction.user.id == interaction.guild.owner.id or interaction.user.id == 888058231094665266:
            await interaction.delete_original_message()
            await interaction.response.send_message('done', ephemeral=True)
            return
        else:
            await interaction.followup.send_message('only owner can do it', ephemeral=True)


class thread_channel(discord.ui.View):
    def __init__(
            self,
            user:discord.Member

    ):
        super().__init__(timeout=1440 * 60)
        self.user = user

    @discord.ui.button(label='archive thread', style=discord.ButtonStyle.green)
    async def archive(self, interaction: discord.Interaction, button):
        if interaction.user.id == self.user.id or interaction.user.guild_permissions.manage_threads:
            await interaction.response.defer(ephemeral=True)
            channel = interaction.channel
            if channel.type == discord.ChannelType.public_thread:
                await channel.edit(archived=True)
            await interaction.delete_original_message()
            return
        else:
            await interaction.response.send_message('this is not for you lol', ephemeral=True)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass
