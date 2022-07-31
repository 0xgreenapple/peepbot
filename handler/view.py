import argparse
import asyncio
import io
import random
import shlex

import aiohttp
import discord

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
        super().__init__(timeout=3600)
        self.message: discord.Message = message
        self.interaction_message = None
        self.member: discord.Member = member
        self.user: discord.Member = user
        self.bot = bot

    @discord.ui.button(label='accept', style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button):
        await interaction.response.defer()

        message = interaction.message
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
        memes = json['data']['memes']
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
        await interaction.message.delete()
        await interaction.followup.send(f'you are ready,lets move!', view=view, ephemeral=True)

    @discord.ui.button(label='cancel', style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button):
        int_message = interaction.message
        await self.message.edit(content=f'{interaction.user.mention} rejected the invite find another participant!',view=None)
        await interaction.message.delete()
        await interaction.response.send_message('successfully canceled the match', ephemeral=True)

    async def on_timeout(self) -> None:
        try:
            embed = discord.Embed(
                title='``timeout``',
                description=f">>> **{self.bot.right} you failed to accept the meme battle invite in time** \n"
                            f"invited by: {self.user.mention}"
            )

            await self.interaction_message.edit(embed=embed, view=None)

        except:
            pass


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
        super().__init__(timeout=10 * 60)
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

        if message2.first:
            first_caption = ' '.join(message2.first)
        if message2.second:
            secondcaption = '' .join(message2.second)
        if message3 is None:
            message3 = ''
        params = {
            'username': 'password',
            'password': 'password',
            'template_id': f'{memeid}',
            'text0': f'{first_caption}',
            'text1': f'{secondcaption}',
        }
        response = await res.request('POST', url, params=params)
        json = await response.json()
        url = json['data']['url']
        image = await res.get(url=url)
        bytes = await image.read()
        file = discord.File(fp=io.BytesIO(bytes), filename='meme.png')
        return file

    async def load_img(self, interaction: discord.Interaction):

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
        memes = json['data']['memes']
        ids = []

        for i in memes:
            if i['box_count'] == '2' or i['box_count'] == 2:
                ids.append(i['id'])

        memeid = await self.bot.db.fetchval(""" SELECT meme_id FROM test.duel WHERE message_id = $1
        """, self.message.id)
        memeid = memeid
        message1 = None
        file = None
        message2 = None
        image_byets = None
        for i in self.memes:
            if i['id'] == f'{memeid}':
                image = await session.get(url=i['url'])
                image_byets = await image.read()
                break

        thread_one = await self.message.channel.create_thread(
            name=f'{self.member.name} room',
            type=discord.ChannelType.public_thread
        )
        thread_two = await self.message.channel.create_thread(
            name=f'{self.user.name} room',
            type=discord.ChannelType.public_thread
        )

        # create dms

        member_channel = await self.member.create_dm()
        user_channel = await self.user.create_dm()

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
            description='>>> you have 10 min to make best meme from this template \n'
                        'run ``$caption --first <your first caption> --second <your second caption>`` \n'
                        'example: **$caption --first yo momma sa fat that she cant even run --second lol**'
        )
        file = discord.File(fp=io.BytesIO(image_byets), filename='memme.png')
        t_one = await thread_one.send(file=file, embed=sendembed)
        file = discord.File(fp=io.BytesIO(image_byets), filename='memme.png')
        t_two = await thread_two.send(file=file, embed=sendembed)

        checks = []
        users_msg = []
        users = []
        first_user_submission = []
        second_user_submission = []

        def check(message: discord.Message) -> bool:
            if self.member.id == self.user.id:
                print('yes')
            args = message.content[8:]
            if message.author.id == self.member.id and message.content.startswith('$caption'):
                parser = Arguments(add_help=False, allow_abbrev=False)
                parser.add_argument('--first','--f',nargs='+')
                parser.add_argument('--second','--s',nargs='+')
                failed = False
                try:
                    args = parser.parse_args(shlex.split(message.content[8:]))
                except Exception as e:
                    self.bot.loop.create_task(message.channel.send(str(e)))
                    failed=True

                if not failed:
                    users_msg.append(f"{message.author.mention} has completed")
                    checks.append(message.author.id)
                    users.append({'message': args, 'id': message.author.id})

            if message.author.id == self.user.id and message.content.startswith('$caption'):
                parser = Arguments(add_help=False, allow_abbrev=False)
                parser.add_argument('--first','--f',nargs='+')
                parser.add_argument('--second','--s',nargs='+')
                failed = False
                args = message.content[8]
                try:
                    args = parser.parse_args(shlex.split(message.content[8:]))
                except Exception as e:
                    self.bot.loop.create_task(message.channel.send(str(e)))
                    failed = True
                if not failed:
                    users_msg.append(f"{message.author.mention} has completed")
                    checks.append(message.author.id)
                    users.append({'message': args, 'id': message.author.id})

            return len(checks) == 2

        try:
            await self.bot.wait_for(f'message', timeout=5*60, check=check)
        except asyncio.TimeoutError:
            if len(users) != 0:
                user_id = users[0]['id']
                user = self.message.guild.get_member(user_id)

                first_user_submission = await self.get_player_img(
                    memeid=memeid, message2=users[0]['message'],
                    url=caption_url
                )
                failed_user = self.user if user.id == self.user else self.member
                await self.message.delete()
                await self.message.channel.send(
                    f'by {user.mention} has won the duel, lmfao {failed_user.mention} failed to make meme in given time',
                    file=first_user_submission
                )
            else:
                await self.message.delete()
                await self.message.channel.send(
                    f'boooooo, {self.user.mention} and {self.member.mention} both failed to make meme in 5 min lol',
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

        await self.message.delete()

        first_submission = await self.message.channel.send(
            f'by {self.user.mention} | vote!',
            file=first_user_submission
        )
        await first_submission.add_reaction("👍")

        second_submission = await self.message.channel.send(
            f'by {self.member.mention} | vote!',
            file=second_user_submission

        )
        await second_submission.add_reaction("👍")
        embeed = discord.Embed(title=f'your meme has been submitted in {self.message.channel.mention} '
                                     f'deleting channel in 3 sec ...')

        await t_one.edit(embeds=[embeed], attachments=[], view=None)
        await t_two.edit(embeds=[embeed], attachments=[], view=None)
        await asyncio.sleep(3)
        self.bot.loop.create_task(thread_one.delete())
        self.bot.loop.create_task(thread_two.delete())

        sleep_until = datetime.now() + timedelta(seconds=60)

        await discord.utils.sleep_until(sleep_until)
        x_msg = await interaction.channel.fetch_message(first_submission.id)
        y_msg = await interaction.channel.fetch_message(second_submission.id)

        count1 = 0
        count2 = 0

        for reaction in x_msg.reactions:
            if reaction.emoji == "👍":
                count1 = reaction.count
                break
        for reaction in y_msg.reactions:
            if reaction.emoji == "👍":
                count2 = reaction.count
                break

        if count1 > count2:
            await second_submission.delete()
            await first_submission.edit(content=f'{self.member.mention} has won the duel by {count1 - count2} votes!')
            await thread_one.delete()
        elif count2 > count1:
            await first_submission.delete()
            await second_submission.edit(content=f'{self.user.mention} has won by {count2 - count1} votes')
            await thread_two.delete()

    @discord.ui.button(label='ready', style=discord.ButtonStyle.green)
    async def ready(self, interaction: discord.Interaction, button):
        if interaction.user.id == self.member.id or interaction.user.id == self.user.id:
            int_message = interaction.message
            messahe = await interaction.response.defer()
            is_user_ready = False
            is_member_ready = False
            member = self.bot.get_user(self.member.id)
            user = self.bot.get_user(self.user.id)
            desc = self.embed_msg.description
            if interaction.user.id == user.id:
                if not is_user_ready:
                    await self.bot.db.execute(
                        """UPDATE test.duel SET member_ready=$1 WHERE message_id = $2""",
                        True, self.message.id
                    )
                else:
                    await interaction.followup.send('you are already ready', ephemeral=True)
            if interaction.user.id == member.id:
                if not is_member_ready:
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

            if member1:
                text.append(f"{member.mention} is ready")
            if use1r:
                text.append(f"{user.mention} is ready")

            if len(text) == 2:
                text1 = '\n'.join(text)

                embed = discord.Embed(title='``duel``',
                                      description=f'>>> you have 10 min to make best meme from '
                                                  f'this template, Click the ready button when you are ready! \n{text1}')
                await self.message.edit(embed=embed, view=None)
                await self.load_img(interaction)

            else:
                text1 = '\n'.join(text)
                embed = discord.Embed(title='``duel``',
                                      description=f'>>> you have 10 min to make best meme from '
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
        print(member_refresh, user_refresh)
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
                    self.bot.loop.create_task(self.bot.db.execute(
                        """UPDATE test.duel SET meme_id = $1 WHERE message_id = $2

                        """, memeid, self.message.id
                    ))
                    break
