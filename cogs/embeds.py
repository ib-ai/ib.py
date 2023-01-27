import asyncio
import logging
import discord
from discord.ext import commands
import json
import re

class Embeds(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

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
                    embed.description = desc.content.strip()[:4096]
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
                    if match is None:
                        await ctx.send("Invalid Format")
                    else:
                        title = match.group(1)[:256]
                        value = match.group(2)[:1024]
                        embed.add_field(name=title, value=value)
                except asyncio.TimeoutError:
                    await ctx.send(INPUT_TIMED_OUT)

        async def get_channel():
            while True:
                try:
                    channel_msg: discord.Message = await self.bot.wait_for("message", check=check, timeout=timeout)
                    if len(channel_msg.channel_mentions) is 0:
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
                msg = await channel.fetch_message(msg_id)
                await msg.edit(embed=embed)
            except discord.HTTPException as ex:
                # TODO: temp. Need to confirm how to handle this correctly.
                await ctx.send("An error occurred while updating the embed.")
                log.error("Error updating embed", ex, exc_info=1)
            except Exception as ex:
                try:
                    await channel.send(embed=embed)
                except Exception as ex:
                    await ctx.send("An error occurred while sending the embed.")
                    log.error("[Embeds.send_or_update_embed]", ex, exc_info=1)

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
        await ctx.send("Should this embed replace any existing message in that channel? If yes, type the message ID, otherwise type anything else.")
        await send_or_update_embed(embed, channel)


    @commands.command()
    async def embedraw(self, ctx: commands.Context, *, embed_data):
        """
        Create a Discord embed via raw JSON input.
        """
        try:
            embed_body = json.loads(embed_data)
            embed = discord.Embed.from_dict(embed_body)
            await ctx.send(embed=embed)
        except Exception as ex:
            print(ex)
            await ctx.send("An Error Occurred")


async def setup(bot: commands.Bot):
    await bot.add_cog(Embeds(bot))