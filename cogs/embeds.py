import asyncio
import logging
import discord
from discord.ext import commands
import json
import re

class Embeds(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DESC_MAX_LEN = 4096
        self.FIELD_TITLE_MAX_LEN = 256
        self.FIELD_VALUE_MAX_LEN = 1024

    @commands.hybrid_command()
    async def embed(self, ctx: commands.Context):
        """
        Interactively construct a Discord embed.
        """

        log = logging.getLogger()
        INPUT_TIMED_OUT = "Input timed out."

        def check(m: discord.Message):
            return m.channel == ctx.channel and m.author == ctx.author

        def is_skip(msg: discord.Message):
            return msg.content.strip().lower() == "skip"

        def is_done(msg: discord.Message):
            return msg.content.strip().lower() == "done"

        async def handle_desc(embed: discord.Embed):
            try:
                desc: discord.Message = await self.bot.wait_for("message", check=check, timeout=timeout)
                if not is_skip(desc): 
                    embed.description = desc.content.strip()[:self.DESC_MAX_LEN]
            except asyncio.TimeoutError:
                await ctx.send(INPUT_TIMED_OUT)

        async def handle_color(embed: discord.Embed):
            while True:
                try:
                    color_msg: discord.Message = await self.bot.wait_for("message", check=check, timeout=timeout)
                    if is_skip(color_msg):
                        break
                    color_str = color_msg.content
                    embed.color = discord.Color.from_str(color_str)
                    break
                except ValueError:
                    await ctx.send("Invalid Color. Please provide the color in hex format (e.g. `#123456`). Use `skip` to skip this.")
                except asyncio.TimeoutError:
                    await ctx.send(INPUT_TIMED_OUT)

        async def handle_img(embed: discord.Embed):
            try:
                img_url_msg: discord.Message = await self.bot.wait_for("message", check=check, timeout=timeout)
                if is_skip(img_url_msg): 
                    return
                img_url = img_url_msg.content.strip()
                if img_url.startswith("<"): 
                    img_url = img_url[1:]
                if img_url.endswith(">"): 
                    img_url = img_url[:-1]
                embed.set_image(url=img_url)
            except asyncio.TimeoutError:
                await ctx.send(INPUT_TIMED_OUT)
            except Exception as ex:
                log.error("[Embeds.handle_img] Error setting image", ex, exc_info=1)

        async def handle_fields(embed: discord.Embed):
            while True:
                try:
                    await ctx.send("You are now adding another field. Please use the following format: `\"Title\" \"Value\"`. You can type `done` to complete the embed.")
                    field_msg = await self.bot.wait_for("message", check=check, timeout=timeout)
                    if is_done(field_msg):
                        break
                    match = re.search('\"(.+?)\" +\"(.+?)\"', field_msg.content.strip())
                    if match == None:
                        await ctx.send("Invalid Format")
                    else:
                        title = match.group(1)[:self.FIELD_TITLE_MAX_LEN]
                        value = match.group(2)[:self.FIELD_VALUE_MAX_LEN]
                        embed.add_field(name=title, value=value)
                except asyncio.TimeoutError:
                    await ctx.send(INPUT_TIMED_OUT)

        async def get_channel():
            while True:
                try:
                    channel_msg: discord.Message = await self.bot.wait_for("message", check=check, timeout=timeout)
                    if len(channel_msg.channel_mentions) == 0:
                        await ctx.send("Could not find that channel")
                    else:
                        channel = channel_msg.channel_mentions[0]
                        return channel
                except asyncio.TimeoutError:
                    await ctx.send(INPUT_TIMED_OUT)
                    break

        async def send_or_update_embed(embed: discord.Embed, channel: discord.TextChannel):
            try:
                msg_id_msg: discord.Message = await self.bot.wait_for("message", check=check, timeout=timeout)
                msg_id = msg_id_msg.content.strip()
                matches = re.match('[0-9]+', msg_id)
                if matches:
                    msg = await channel.fetch_message(msg_id)
                    await msg.edit(embed=embed)
                    return
                await channel.send(embed=embed)
            except discord.NotFound as ex:
                await ctx.send("No message with this ID was found.")
            except discord.HTTPException as ex:
                # TODO: temp. Need to confirm how to handle this correctly.
                await ctx.send("An error occurred while updating/sending the embed.")
                log.error("Error updating/sending embed: %s", ex, exc_info=1)
            except Exception as ex:
                await ctx.send("An error occurred.")
                log.error(ex)

        timeout = 60
        embed = discord.Embed()
        
        await ctx.send("Please type the description of the embed. Use `skip` to skip this.")
        await handle_desc(embed)
        await ctx.send("Please provide the colour in hex format (e.g. `#123456`). Use `skip` to skip this.")
        await handle_color(embed)
        await ctx.send("Please provide the URL for the image you would like to display. Use `skip` to skip this.")
        await handle_img(embed)
        await handle_fields(embed)
        await ctx.send("Which channel should the embed be sent in?")
        channel = await get_channel()
        member_perms = channel.permissions_for(ctx.author)
        if not (member_perms.send_messages and member_perms.embed_links):
            await ctx.send("Missing channel permissions.")
            return
        await ctx.send("Should this embed replace any existing message in that channel? If yes, type the message ID, otherwise type anything else.")
        await send_or_update_embed(embed, channel)


    @commands.command()
    async def embedraw(self, ctx: commands.Context, type, channel, *argv):
        """
        Create a Discord embed via raw JSON input.
        """

        # NOTE: This breaks if we miss type or channel as it tries to parse the JSON body in those and breaks. IDK how to fix.

        log = logging.getLogger()
        embed_data = None
        msg_id = None
        print(type, channel, argv)

        # try:

        #     if type == "create":
        #         if len(argv) != 1:
        #             await ctx.send('Invalid arguments. Please use the following format: `create <#channel> <embed_data>`.')
        #             return
        #         embed_data = argv[0]
        #     elif type == "update":
        #         if len(argv) != 2:
        #             await ctx.send('Invalid arguments. Please use the following format: `update <#channel> <message_id> <embed_data>`.')
        #             return
        #         msg_id = argv[0].strip()
        #         embed_data = argv[1]
        #     else:
        #         await ctx.send('Unidentified type. Please use either `create` or `update` as the type.')
        #         return

        #     member_perms = channel.permissions_for(ctx.author)
        #     if not (member_perms.send_messages and member_perms.embed_links):
        #         await ctx.send("Missing channel permissions.")
        #         return

        #     raw = json.loads(embed_data)
        #     embed = discord.Embed()

        #     if 'description' in raw:
        #         embed.description = raw['description'].strip()[:self.DESC_MAX_LEN]
            
        #     if 'colour' in raw:
        #         try:
        #             embed.color = embed.color = discord.Color.from_str(raw['colour'])
        #         except ValueError as ex:
        #             await ctx.send('Invalid Color. Please provide the color in hex format (e.g. `#123456`).')
        #             return

        #     if 'image_url' in raw:
        #         img_url = raw['image_url'].content.strip()
        #         if img_url.startswith("<"): 
        #             img_url = img_url[1:]
        #         if img_url.endswith(">"): 
        #             img_url = img_url[:-1]
        #         embed.set_image(url=img_url)

        #     if 'fields' in raw:
        #         fields = raw['fields']
        #         if len(fields) > 20:
        #             await ctx.send("")
        #             return
                
        #         for tuple in fields:
        #             if len(tuple) > 2:
        #                 continue
        #             title, value = tuple
        #             title = title[:self.FIELD_TITLE_MAX_LEN]
        #             value = value[:self.FIELD_VALUE_MAX_LEN]
        #             embed.add_field(name=title, value=value)

        #     if type == "update":
        #         msg = await channel.fetch_message(msg_id)
        #         await msg.edit(embed=embed)
        #         return

        #     await channel.send(embed=embed)

        # except commands.errors.MissingRequiredArgument as ex:
        #     await ctx.send('Invalid arguments.')
        # except commands.errors.ChannelNotFound as ex:
        #     await ctx.send('Channel not found.')
        # except discord.NotFound as ex:
        #     await ctx.send('Message with that ID was not found in the target channel.')
        # except discord.HTTPException as ex:
        #     await ctx.send("An error occurred while updating/sending the embed.")
        #     log.error("Error updating/sending embed: %s", ex, exc_info=1)
        # except ex:
        #     await ctx.send('An error occurred.')
        #     log.error(ex)

async def setup(bot: commands.Bot):
    await bot.add_cog(Embeds(bot))