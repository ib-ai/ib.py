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

        def check(m: discord.Message):
            return m.channel == ctx.channel and m.author == ctx.author

        def is_skip(msg: discord.Message):
            return msg.content.strip().lower() == "skip"

        def is_done(msg: discord.Message):
            return msg.content.strip().lower() == "done"


        async def handle_color(embed: discord.Embed):
            while True:
                try:
                    color_msg: discord.Message = await self.bot.wait_for("message", check=check, timeout=timeout)
                    if is_skip(color_msg):
                        break
                    color_str = color_msg.content
                    embed.color = discord.Color.from_str(color_str)
                    break
                except:
                    await ctx.send("Invalid Color. Please provide the color in hex format (e.g. `#123456`). Use `skip` to skip this.")

        async def handle_img(embed: discord.Embed):
            img_url_msg: discord.Message = await self.bot.wait_for("message", check=check, timeout=timeout)
            if is_skip(img_url_msg): return
            img_url = img_url_msg.content.strip()
            if img_url.startswith("<"): img_url = img_url[1:]
            if img_url.endswith(">"): img_url = img_url[:-1]
            try:
                embed.set_image(url=img_url)
            except:
                print("Error setting image")

        async def handle_fields(embed: discord.Embed):
            while True:
                await ctx.send("You are now adding another field. Please use the following format: `\"Title\" \"Value\"`. You can type `done` to complete the embed.")
                field_msg = await self.bot.wait_for("message", check=check, timeout=timeout)
                if is_done(field_msg):
                    break
                [title, value] = await handle_field(field_msg)
                title = title[:256]
                value = value[:1024]
                embed.add_field(name=title, value=value)

        async def handle_field(field_msg: discord.Message):
            output = []
            current = None
            field_tokens = re.split(" +", field_msg.content.strip())

            for token in field_tokens:
                if token.startswith("\"") and current is None:
                    current = ""
                
                if current is not None:
                    current = current + token + " "
                
                if token.endswith("\"") and current is not None:
                    index = len(token) - 2
                    if index < 0 or token[index] != "\\":
                        data = current.strip()
                        data = data[1:-1]
                        output.append(data)
                        current = None

            return output

        async def handle_channel():
            while True:
                try:
                    channel_msg: discord.Message = await self.bot.wait_for("message", check=check, timeout=timeout)
                    if len(channel_msg.channel_mentions) is 0:
                        await ctx.send("Could not find that channel")
                    else:
                        channel = channel_msg.channel_mentions[0]
                        return channel
                except TimeoutError:
                    await ctx.send("Reached Timeout. Discarding Embed")
                    break

        async def handle_replacement_msg(embed: discord.Embed, channel: discord.TextChannel):
            msg_id_msg: discord.Message = await self.bot.wait_for("message", check=check, timeout=timeout)
            msg_id = msg_id_msg.content.strip()
            try:
                msg = await channel.fetch_message(msg_id)
                await msg.edit(embed=embed)
            except:
                await channel.send(embed=embed)

        timeout = 60 * 1000
        embed = discord.Embed()
        
        await ctx.send("Please type the description of the embed. Use `skip` to skip this.")
        desc: discord.Message = await self.bot.wait_for("message", check=check, timeout=timeout)
        if not is_skip(desc): embed.description = desc.content.strip()[:4096]

        await ctx.send("Please provide the colour in hex format (e.g. `#123456`). Use `skip` to skip this.")
        await handle_color(embed)

        await ctx.send("Please provide the URL for the image you would like to display. Use `skip` to skip this.")
        await handle_img(embed)

        await handle_fields(embed)
        
        await ctx.send("Which channel should the embed be sent in?")
        channel = await handle_channel()

        await ctx.send("Should this embed replace any existing message in that channel? If yes, type the message ID, otherwise type anything else.")
        await handle_replacement_msg(embed, channel)


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