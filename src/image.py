import re
import cv2
import aiohttp
import asyncio
import numpy as np
from os import path
from io import BytesIO
from random import randint
from PIL import Image, ImageFont, ImageDraw
from hoshino import aiorequests
from concurrent.futures import ThreadPoolExecutor

from .utils import img_to_cvimg, cvimg_to_img, cvimg_to_base64, img_to_base64
from .head_source import detect_face, gen_head, concat

high_eq_path = path.join(path.dirname(__file__), '../images/high_eq_image.png')
high_eq_font_path = path.join(path.dirname(__file__), '../fonts/NotoSansCJKSC-Black.ttf')
concat_head_cascade = cv2.CascadeClassifier(path.join(path.dirname(__file__), "../models/lbpcascade_animeface.xml"))


def draw_text(img_pil, text, offset_x):
    draw = ImageDraw.Draw(img_pil)
    font = ImageFont.truetype(high_eq_font_path, 48)
    width, height = draw.textsize(text, font)
    x = 5
    if width > 390:
        font = ImageFont.truetype(high_eq_font_path, int(390 * 48 / width))
        width, height = draw.textsize(text, font)
    else:
        x = int((400 - width) / 2)
    draw.rectangle((x + offset_x - 2, 360, x + 2 + width + offset_x, 360 + height * 1.2), fill=(0, 0, 0, 255))
    draw.text((x + offset_x, 360), text, font=font, fill=(255, 255, 255, 255))


async def get_jl(index, jl, px, bottom):
    data = {
        'id': jl,
        'zhenbi': '20191123',
        'id2': '18',
        'id5': '10',
        'id7': bottom,
    }
    if index == '盘旋':
        subfix = '111'
        data['id1'] = '9007'
        data['id3'] = '#0000FF'
        data['id4'] = '#FF0000'
        data['id8'] = '9005'
        data['id10'] = px
        data['id11'] = 'jiqie.com_2'
        data['id12'] = '241'
    elif index == '飞升':
        subfix = '111'
        data['id1'] = '9005'
        data['id3'] = '#00FF00'
        data['id4'] = '#FFFF00'
        data['id8'] = '9008'
        data['id10'] = px
        data['id11'] = 'jiqie.com_1'
        data['id12'] = '505'
    elif index == '酷炫':
        subfix = '102'
        data['id1'] = '9005'
        data['id3'] = '#CDE374'
        data['id4'] = '#4CA3CF'
        data['id8'] = '9007'
    else:
        return None
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36', 'Content-type': 'application/x-www-form-urlencoded'}
    async with aiohttp.request(method='POST', url=f"http://jiqie.zhenbi.com/e/re{subfix}.php", headers=headers, data=data) as resp:
        t = await resp.text()
        regex = r'<img src="(.+)">'
        return re.match(regex, t).groups()[0]


def head_detect_cv(img: Image):
    cvimg = img_to_cvimg(img)
    gray = cv2.cvtColor(cvimg, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    return concat_head_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(24, 24))


async def head_detect_yolo(img: Image):
    cvimg = img_to_cvimg(img)
    image_base64 = cvimg_to_base64(cvimg)
    resp = await aiorequests.post('http://10.8.14.221:2334/anime_head_detect', json={'image': image_base64})
    if resp is not None and resp.status_code == 200:
        res = await resp.json()
        if 'result' in res:
            return res['result']
    return None


async def concat_head_(img: Image):
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor()

    top_shift_scale = 0.25
    x_scale = 0.15
    faces = await head_detect_yolo(img)
    if faces is not None and len(faces) > 0:
        faces = await loop.run_in_executor(executor, head_detect_cv, img)
        if not len(faces):
            return Image.open(path.join(path.dirname(__file__), "../images/head/没找到头.png"))
        else:
            top_shift_scale = 0.45
            x_scale = 0.25
    img = img.convert("RGBA")

    for (x, y, w, h) in faces:
        y_shift = int(h * top_shift_scale)
        x_shift = int(w * x_scale)
        face_w = max(w + 2 * x_shift, h + y_shift)
        faceimg = Image.open(path.join(path.dirname(__file__), "../images/head/猫猫头_" + str(randint(0, 6)) + ".png"))
        faceimg = faceimg.resize((face_w, face_w))
        r, g, b, a = faceimg.split()
        img.paste(faceimg, (x - x_shift, y - y_shift), mask=a)
    return img


async def concat_head_real_(img: Image):
    b64 = img_to_base64(img)
    face_data_list = await detect_face(b64)
    if not face_data_list:
        return Image.open(path.join(path.dirname(__file__), '../images/head/接头失败.png'))
    head_gener = gen_head()
    for dat in face_data_list:
        try:
            head = head_gener.__next__()
        except StopIteration:
            head_gener = gen_head()
            head = head_gener.__next__()
        img = concat(img, head, dat)
        return img


def make_hide_image(up_img, hide_img):
    up_img = img_to_cvimg(up_img)
    hide_img = img_to_cvimg(hide_img)

    max_size = (0, max(up_img.shape[1], hide_img.shape[1]))
    up_img = cv2.resize(up_img, (max_size[1], int(up_img.shape[0] * (max_size[1] / up_img.shape[1]))))
    hide_img = cv2.resize(hide_img, (max_size[1], int(hide_img.shape[0] * (max_size[1] / hide_img.shape[1]))))
    max_size = (max(up_img.shape[0], hide_img.shape[0]), max_size[1])

    if hide_img.shape[0] == up_img.shape[0]:
        pass
    elif max_size[0] == hide_img.shape[0]:
        up_img_temp = np.ones((*max_size, 3), dtype=np.float32)
        x = (max_size[0] - up_img.shape[0]) // 2
        up_img_temp[x:x + up_img.shape[0], :, :] = up_img
        up_img = up_img_temp.copy()
    elif max_size[0] == up_img.shape[0]:
        hide_img_temp = np.zeros((*max_size, 3), dtype=np.float32)
        x = (max_size[0] - hide_img.shape[0]) // 2
        hide_img_temp[x:x + hide_img.shape[0], :, :] = hide_img
        hide_img = hide_img_temp.copy()

    up_img = cv2.cvtColor(up_img, cv2.COLOR_BGR2GRAY)
    hide_img = cv2.cvtColor(hide_img, cv2.COLOR_BGR2GRAY)

    imgLa = up_img.astype(np.float32) / 512 + 0.5
    imgLb = hide_img.astype(np.float32) / 512

    R = 255 * imgLb / (1 - (imgLa - imgLb))
    a = (1 - (imgLa - imgLb)) * 255
    out = cv2.merge((R, R, R, a))

    return cvimg_to_img(out.astype(np.uint8))


def make_hide_image_color(up_img, hide_img):
    up_img = img_to_cvimg(up_img)
    hide_img = img_to_cvimg(hide_img)

    max_size = (0, max(up_img.shape[1], hide_img.shape[1]))
    up_img = cv2.resize(up_img, (max_size[1], int(up_img.shape[0] * (max_size[1] / up_img.shape[1]))))
    hide_img = cv2.resize(hide_img, (max_size[1], int(hide_img.shape[0] * (max_size[1] / hide_img.shape[1]))))
    max_size = (max(up_img.shape[0], hide_img.shape[0]), max_size[1])

    up_img = up_img.astype(np.float32) / 255
    hide_img = hide_img.astype(np.float32) / 255

    if hide_img.shape[0] == up_img.shape[0]:
        pass
    elif max_size[0] == hide_img.shape[0]:
        up_img_temp = np.ones((*max_size, 3), dtype=np.float32)
        x = (max_size[0] - up_img.shape[0]) // 2
        up_img_temp[x:x + up_img.shape[0], :, :] = up_img
        up_img = up_img_temp.copy()
    elif max_size[0] == up_img.shape[0]:
        hide_img_temp = np.zeros((*max_size, 3), dtype=np.float32)
        x = (max_size[0] - hide_img.shape[0]) // 2
        hide_img_temp[x:x + hide_img.shape[0], :, :] = hide_img
        hide_img = hide_img_temp.copy()

    m_lightWhite, m_lightBlack = 1.0, 0.2
    m_colorWhite, m_colorBlack = 0.5, 0.7
    up_img = up_img * m_lightWhite
    hide_img = hide_img * m_lightBlack
    gray1 = cv2.cvtColor(up_img, cv2.COLOR_BGR2GRAY)
    gray1 = cv2.cvtColor(gray1, cv2.COLOR_GRAY2BGR)
    img1 = up_img * m_colorWhite + gray1 * (1 - m_colorWhite)
    gray2 = cv2.cvtColor(hide_img, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(gray2, cv2.COLOR_GRAY2BGR)
    img2 = hide_img * m_colorBlack + gray2 * (1 - m_colorBlack)
    imgd = 1 - img1 + img2
    maxc = np.max(hide_img, axis=2)
    a = cv2.cvtColor(imgd, cv2.COLOR_BGR2GRAY)
    a = np.clip(a, maxc, 1)
    a_c = cv2.cvtColor(a, cv2.COLOR_GRAY2BGR)
    out = np.clip(hide_img / a_c, 0, 1)
    out = cv2.merge((*cv2.split(out), a)) * 255

    return cvimg_to_img(out.astype(np.uint8))
