import vk_api
from vk_api.bot_longpoll import VkBotLongPoll

from config import GROUP_ID, TOKEN


# Creates a fresh VK session, API client, and Long Poll transport.
def create_vk_transport():
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)
    return vk_session, vk, longpoll


vk_session, vk, longpoll = create_vk_transport()
