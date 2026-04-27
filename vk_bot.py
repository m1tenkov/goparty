import vk_api
from vk_api.bot_longpoll import VkBotLongPoll

from config import GROUP_ID, TOKEN

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()


# Создает новый экземпляр Long Poll для переподключения после сбоев.
def create_longpoll():
    return VkBotLongPoll(vk_session, GROUP_ID)


longpoll = create_longpoll()
