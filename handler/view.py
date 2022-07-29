import asyncio
import io
import random
import time
from datetime import datetime, timedelta

import aiohttp
import discord
from discord import Button
from discord.ui import View

import pepebot


class duel_button(discord.ui.View):
    def __init__(self,
                 message: discord.Message,
                 member: discord.Member,
                 user: discord.Member,
                 bot: pepebot.pepebot
                 ):
        super().__init__(timeout=180)
        self.message: discord.Message = message
        self.member: discord.Member = member
        self.user: discord.Member = user
        self.bot = bot

    @discord.ui.button(label='accept', style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        await self.bot.db.execute(
            """INSERT INTO test.duel(user_id1,user_id2,message_id)
            VALUES($1,$2,$3)
            """, self.user.id, self.member.id, self.message.id

        )
        message = interaction.message
        sent_message_url = self.message.jump_url

        view = ready_button(member=self.member, user=self.user, bot=self.bot, message=self.message)
        await self.message.edit(content=f'{interaction.user.mention} has been accepted the invite click on '
                                        f'ready to be ready', view=view)
        view = View()
        url = discord.ui.Button(url=sent_message_url,label='your room')
        view.add_item(url)
        await interaction.followup.send(f'you are ready lets move to the message : {sent_message_url}',view=view)

    @discord.ui.button(label='cancel', style=discord.ButtonStyle.green)
    async def cancel(self, interaction: discord.Interaction, button):
        int_message = interaction.message

        await self.message.edit(content=f'{interaction.user.mention} rejected the invite find another participant?')
        await interaction.response.send_message('successfully canceled the match')


class ready_button(discord.ui.View):
    def __init__(self,
                 message: discord.Message,
                 member: discord.Member,
                 user: discord.Member,
                 bot: pepebot.pepebot
                 ):
        super().__init__(timeout=180)
        self.message: discord.Message = message
        self.member: discord.Member = member
        self.user: discord.Member = user
        self.bot = bot

    async def get_player_img(self, memeid, message2, message3: str = None, *, url):
        res: aiohttp.ClientSession = self.bot.aiohttp_session
        if message3 == None:
            message3 = ''
        params = {
            'username': '0xgreenapple',
            'password': 'galax7361',
            'template_id': f'{memeid}',
            'text0': f'{message2}',
            'text1': f'{message3}',
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
        a = await session.request(method='GET', url='https://api.imgflip.com/get_memes')
        json = await a.json()
        memes = json['data']['memes']
        ids = []

        for i in memes:
            if i['box_count'] == '2' or i['box_count'] == 2:
                ids.append(i['id'])

        memeid = random.choice(ids)
        message1 = None
        file = None
        message2 = None
        image_byets = None

        for i in memes:
            if i['id'] == f'{memeid}':
                image = await session.get(url=i['url'])
                image_byets = await image.read()
                file = discord.File(fp=io.BytesIO(image_byets), filename='memme.png')
                message1 = await self.message.edit(
                    content=f"{self.member.mention} {self.user.mention} you have 10 min to make "
                            f"best meme from this template check your dms"
                    , attachments=[file])
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

        embed = discord.Embed(title='click_me', url=thread_one.jump_url)
        embed2 = discord.Embed(title='click_me', url=thread_two.jump_url)

        await member_channel.send(f"you have 10 mins to make meme from the template here is your room run $caption "
                                  f"<yourcaption> <secondcaption>", embed=embed)
        await user_channel.send(f"you have 10 mins to make meme from the template here is your room run $caption "
                                f"<yourcaption> <secondcaption>", embed=embed2)

        file = discord.File(fp=io.BytesIO(image_byets), filename='memme.png')
        await thread_one.send(file=file)
        file = discord.File(fp=io.BytesIO(image_byets), filename='memme.png')
        await thread_two.send(file=file)
        checks = []
        users_msg = []
        users = []
        first_user_submission = []
        second_user_submission = []

        def check(message: discord.Message) -> bool:
            if self.member.id == self.user.id:
                print('yes')
            if message.author.id == self.member.id and message.content.startswith('$caption'):
                users_msg.append(f"{message.author.mention} has completed")
                checks.append(message.author.id)
                users.append({'message': message.content[8:], 'id': message.author.id})

            if message.author.id == self.user.id and message.content.startswith('$caption'):
                users_msg.append(f"{message.author.mention} has completed")
                checks.append(message.author.id)
                users.append({'message': message.content[8:], 'id': message.author.id})

            print(f'second lenth {len(checks)}')
            return len(checks) == 2

        await self.bot.wait_for(f'message', timeout=None, check=check)

        if users[0]['id'] == self.user.id:
            first_user_submission = await self.get_player_img(memeid=memeid, message2=users[0]['message'],
                                                              url=caption_url)
        elif users[0]['id'] == self.member.id:
            second_user_submission = await self.get_player_img(memeid=memeid, message2=users[0]['message'],
                                                               url=caption_url)

        if users[1]['id'] == self.user.id:
            first_user_submission = await self.get_player_img(memeid=memeid, message2=users[1]['message'],
                                                              url=caption_url)
        elif users[1]['id'] == self.member.id:
            second_user_submission = await self.get_player_img(memeid=memeid, message2=users[1]['message'],
                                                               url=caption_url)

        print(first_user_submission)
        print(second_user_submission)

        first_submission = await message1.channel.send(f'by {self.user.mention} | mention',
                                                       file=first_user_submission)
        await first_submission.add_reaction("👍")

        second_submission = await message1.channel.send(f'by {self.member.mention} | mention',
                                                        file=second_user_submission)
        await second_submission.add_reaction("👍")

        sleep_until = datetime.now() - timedelta(seconds=10)

        await asyncio.sleep(10)
        x_msg = await interaction.channel.fetch_message(first_submission.id)
        y_msg =  await interaction.channel.fetch_message(second_submission.id)

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
            await first_submission.edit(content=f'{self.member.mention} has won by {count1 - count2} votes')
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
            if interaction.user.id == user.id:
                if not is_user_ready:
                    await self.bot.db.execute("""
                        UPDATE test.duel SET member_ready=$1 WHERE message_id = $2
                    """, True, self.message.id)
                    is_user_ready = True
                else:
                    await interaction.followup.send('you are already ready', ephemeral=True)
            if interaction.user.id == member.id:
                if not is_member_ready:
                    await self.bot.db.execute("""
                                    UPDATE test.duel SET user_ready=$1 WHERE message_id = $2
                                """, True, self.message.id)
                    is_member_ready = True
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
                message = '\n'.join(text)
                await self.message.edit(content=f"{message} \n loading ....", view=None)
                await self.load_img(interaction)

            else:
                await self.message.edit(content='\n'.join(text))
        else:
            await interaction.response.send_message(f'this is not for you!', ephemeral=True)
