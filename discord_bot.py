import asyncio
import re
import requests
import urllib.request
import vk_api
from discord.ext import commands
from discord import Embed, Intents
from settings import config


class DiscordVkCheckerBot(commands.Bot):
    def __init__(self, prefix, app_info_getter):
        intents = Intents.all()
        commands.Bot.__init__(self, command_prefix=prefix, intents=intents)
        self.vk = app_info_getter

        @self.command(name="get_info")
        async def get_info(ctx):
            await ctx.reply("```Введите ссылку на страницу пользователя или сообщества ВКонтакте.```")
            try:
                url = await self.wait_for("message")
                name = self.get_name_from_url(url.content)
                page = self.check_name(name)

                if not page:
                    await ctx.reply("```Ссылка недействительна.```")

                if page["type"] == "user":
                    user_data = self.vk.users.get(user_ids=page["object_id"], fields=["has_photo", "photo_400_orig"])
                    user_info = self.get_user_info(user_data)
                    image = self.get_user_avatar(user_data)
                    await ctx.reply(f"{user_info}")
                    await ctx.reply(embed=image)

                elif page["type"] == "group":
                    group_data = self.vk.groups.getById(group_id=page["object_id"], fields=["has_photo", "photo_400_orig"])
                    group_info = self.get_group_info(group_data)
                    image = self.get_group_avatar(group_data)
                    await ctx.reply(f"{group_info}")
                    await ctx.reply(embed=image)

            except asyncio.TimeoutError:
                await ctx.reply("```Повторите запрос.```")

    def get_name_from_url(self, url: str) -> str:
        return url.split("/vk.com/")[-1]

    def check_name(self, name: str) -> dict:
        params = {
            "access_token": config["vk_app_token"],
            "screen_name": name,
            "v": config["version"]
            }
        response = requests.get(
            url="https://api.vk.com/method/utils.resolveScreenName?",
            params=params
            ).json()

        return response['response']

    def get_user_info(self, user_info: list) -> str:
        url_type = "Запрашиваемый адрес является адресом пользователя."
        id_user = user_info[0]["id"]

        first_name = user_info[0]["first_name"]
        last_name = user_info[0]["last_name"]
        full_name = " ".join(["Имя пользователя:", first_name, last_name])

        user_ID = " ".join(["ID пользователя:", str(id_user)])

        reg_date = self.get_reg_date(id_user)

        all_info = "\n".join([
            url_type,
            full_name,
            user_ID,
            reg_date
        ])
        return all_info

    def get_reg_date(self, id_user: int) -> str:
        user_profile_link = f"https://vk.com/foaf.php?id={id_user}"

        with urllib.request.urlopen(user_profile_link) as response:
            user_profile_xml = response.read().decode("windows-1251")

        reg_date = re.findall(r'date="(.*)"', user_profile_xml)[0]
        reg_day_info = f"{reg_date[8:10]}/{reg_date[5:7]}/{reg_date[0:4]}"
        reg_time_info = f"{int(reg_date[11:13]) + 1}:{reg_date[14:16]}:{reg_date[17:19]}"
        return f"Зарегистрирован: {reg_day_info} - {reg_time_info}."

    def get_user_avatar(self, user):
        image = Embed()
        if not user[0]["has_photo"]:
            title = "```Пользователь не установил аватар.```"
        else:
            title = "```Аватар пользователя:```"
            image.set_image(url=user[0]["photo_400_orig"])
        image.add_field(name="", value=title)
        return image

    def get_group_info(self, group_info):
        url_type = "Запрашиваемый адрес является адресом группы."

        group_name = " ".join(["Название группы:", group_info[0]["name"]])

        group_ID = " ".join(["ID группы:", str(group_info[0]["id"])])

        all_info = "\n".join([
            url_type,
            group_name,
            group_ID
        ])
        return all_info

    def get_group_avatar(self, group):
        image = Embed()
        if not group[0]["has_photo"]:
            title = "```В группе не установлен аватар.```"
        else:
            title = "```Аватар группы:```"
            image.set_image(url=group[0]["photo_400_orig"])
        image.add_field(name="", value=title)
        return image


if __name__ == "__main__":
    print("Бот запущен.")
    vk_app_helper = vk_api.VkApi(token=config["vk_app_token"])
    vk_app_info = vk_app_helper.get_api()

    discord_bot = DiscordVkCheckerBot(
        prefix=config["prefix"],
        app_info_getter=vk_app_info)
    discord_bot.run(config["discord_token"])
