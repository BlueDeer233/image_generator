import cv2
import json
import base64
import numpy as np
from io import BytesIO
from PIL import Image
from hoshino import aiorequests
from hoshino.log import new_logger
from hoshino.typing import HoshinoBot, CQEvent

logger = new_logger('image_generator', debug=False)

headers = {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.6) ",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
           "Accept-Language": "zh-cn"
           }


def img_to_cvimg(img: Image):
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def cvimg_to_img(cvimg: np.ndarray):
    if cvimg.shape[-1] == 4:
        return Image.fromarray(cv2.cvtColor(cvimg, cv2.COLOR_BGRA2RGBA))
    else:
        return Image.fromarray(cv2.cvtColor(cvimg, cv2.COLOR_BGR2RGB))


def cvimg_to_base64(image_np):
    image = cv2.imencode('.jpg', image_np)[1]
    image_code = str(base64.b64encode(image))[2:-1]
    return image_code


def img_to_base64(img: Image):
    output_buffer = BytesIO()
    img.save(output_buffer, format='JPEG')
    byte_data = output_buffer.getvalue()
    base64_str = base64.b64encode(byte_data)
    return base64_str


def get_all_img_url(event: CQEvent):
    all_url = []
    for i in event["message"]:
        if i["type"] == "image":
            all_url.append(i["data"]["url"])
    return all_url


async def save_img(image_url):
    image = []
    try:
        if len(image_url) == 0:
            return None
        for url in image_url:
            response = await aiorequests.get(url, headers=headers)
            image.append(Image.open(BytesIO(await response.content)))
        return image
    except Exception as e:
        print(repr(e))
        return None


def load_config(path):
    try:
        with open(path, mode='r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except Exception as ex:
        logger.error(f'exception occured when loading config in {path}  {ex}')
        logger.exception(ex)
        return {}


async def get_image(bot: HoshinoBot, ev: CQEvent):
    try:
        index = list(map(lambda x: x.type == "image", ev.message)).index(True)
    except ValueError:
        index = -1
    if index >= 0:
        url = ev.message[index]['data']['url']
        resp = await aiorequests.get(url)
        resp_cont = await resp.content
        try:
            image = Image.open(BytesIO(resp_cont))
            return image
        except:
            return None
    else:
        try:
            index = list(map(lambda x: x.type == "reply", ev.message)).index(True)
        except ValueError:
            index = -1
        if index >= 0:
            msg_id = ev.message[index]['data']['id']
            reply_msg = (await bot.get_msg(message_id=msg_id))['message']
            try:
                index = list(map(lambda x: x['type'] == "image", reply_msg)).index(True)
            except ValueError:
                index = -1
            if index >= 0:
                url = reply_msg[index]['data']['url']
                resp = await aiorequests.get(url)
                resp_cont = await resp.content
                try:
                    image = Image.open(BytesIO(resp_cont))
                    return image
                except:
                    return None
    return None
