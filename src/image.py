import re
import cv2
import aiohttp
import asyncio
from os import path
from io import BytesIO
from random import randint
from PIL import Image, ImageFont, ImageDraw
from hoshino import aiorequests
from concurrent.futures import ThreadPoolExecutor

from .utils import img_to_cvimg, cvimg_to_base64, img_to_base64
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
    # 先获取两张图片中宽度较大的宽度
    max_size = (max(up_img.size[0], hide_img.size[0]), 0)
    # 将图片依据较大的宽度等比例处理
    up_img = up_img.resize((max_size[0], int(up_img.size[1] * (max_size[0] / up_img.size[0]))), Image.ANTIALIAS)
    hide_img = hide_img.resize((max_size[0], int(hide_img.size[1] * (max_size[0] / hide_img.size[0]))), Image.ANTIALIAS)
    # 获取处理后生成图片的大小
    max_size = (max_size[0], max(up_img.size[1], hide_img.size[1]))

    if hide_img.size[1] == up_img.size[1]:  # 大小相等直接转为灰度图片
        up_img = up_img.convert('L')
        hide_img = hide_img.convert('L')
    elif max_size[1] == hide_img.size[1]:  # 这两个elif都是对图片进行大小补全后再转为灰度图片
        up_img_temp = Image.new('RGBA', (max_size), (255, 255, 255, 255))
        up_img_temp.paste(up_img, (0, (max_size[1] - up_img.size[1]) // 2))
        up_img = up_img_temp.convert('L')
        hide_img = hide_img.convert('L')
    elif max_size[1] == up_img.size[1]:
        hide_img_temp = Image.new('RGBA', (max_size), (0, 0, 0, 255))
        hide_img_temp.paste(hide_img, (0, (max_size[1] - hide_img.size[1]) // 2))
        up_img = up_img.convert('L')
        hide_img = hide_img_temp.convert('L')

    out = Image.new('RGBA', (max_size), (255, 255, 255, 255))  # 生成一个空的用于输出的图片
    for i in range(up_img.size[0]):
        for k in range(up_img.size[1]):  # 遍历读取每一个像素点
            La = (up_img.getpixel((i, k)) / 512) + 0.5  # 512是256*2，采用256是为了避免La-Lb=1的情况，而且基本不会损失图片信息
            Lb = hide_img.getpixel((i, k)) / 512  # a/2 +0.5是为了区分明部和暗部，这样明部都在[0.5,1),暗部都在[0,0.5)，互不干扰
            R = int((255 * Lb) / (1 - (La - Lb)))
            a = int((1 - (La - Lb)) * 255)  # 这里是套用公式 公式可以见b站专栏 隐藏图原理(https://www.bilibili.com/read/cv9474134/)
            out.putpixel((i, k), (R, R, R, a))  # 将用于输出的图片每个像素点处理成需要的颜色和透明度

    return out
