import vk_api

from config import TOKEN, VK_API_VERSION


def create_vk_api():
    vk_session = vk_api.VkApi(token=TOKEN, api_version=VK_API_VERSION)
    return vk_session.get_api()
