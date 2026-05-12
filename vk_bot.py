import vk_api

from config import TOKEN


def create_vk_api():
    vk_session = vk_api.VkApi(token=TOKEN)
    return vk_session.get_api()
