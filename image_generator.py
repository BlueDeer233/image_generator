import os
import asyncio
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

from hoshino import Service, priv
from hoshino.typing import HoshinoBot, CQEvent, MessageSegment, CommandSession
from hoshino.util import FreqLimiter, DailyNumberLimiter, pic2b64

from .src.generator import genImage
from .src.image import high_eq_path, draw_text, get_jl, concat_head_, concat_head_real_, make_hide_image
from .src.utils import save_img, get_all_img_url
from hoshino.modules.image_generator.src.utils import get_image

_max = 10
_time = 60
EXCEED_NOTICE = f'您今天已经使用{_max}次了，休息一下明天再来吧~'
_nlmt = DailyNumberLimiter(_max)
_flmt = FreqLimiter(_time)

HELP_MSG = '''
[5000兆元|5000兆円|5kcy] (上半句) (下半句)
低情商 <文本> 高情商 <文本>
金龙盘旋 <文字1> <文字2> <底部文字>
金龙飞升 <文字1> <文字2> <底部文字>
金龙酷炫 <文字> <底部文字>
接头 <图片>
real接头 <图片>
@bot 隐藏图片
'''.strip()
sv = Service('生草图片生成器', help_=HELP_MSG)


@sv.on_prefix(('5000兆元', '5000兆円', '5kcy'))
async def gen_5000_pic(bot: HoshinoBot, ev: CQEvent):
    uid = ev.user_id
    gid = ev.group_id
    if not _nlmt.check(uid):
        await bot.finish(ev, EXCEED_NOTICE, at_sender=True)
    if not _flmt.check(uid):
        await bot.finish(ev, f'您冲的太快了,{round(_flmt.left_time(uid))}秒后再来吧', at_sender=True)
    try:
        keyword = ev.message.extract_plain_text().strip()
        args = ev.message.extract_plain_text().strip().split()
        if len(args) != 2:
            await bot.finish(ev, f"5000兆元需要两个参数")
        upper = args[0]
        downer = args[1]
        img = genImage(word_a=upper, word_b=downer)
        img = str(MessageSegment.image(pic2b64(img)))
        await bot.send(ev, img, at_sender=True)
        _nlmt.increase(uid)
    except OSError:
        await bot.send(ev, '生成失败……请检查字体文件设置是否正确')
    except:
        await bot.send(ev, '生成失败……请检查命令格式是否正确')


@sv.on_rex('低情商(?P<left>.+)高情商(?P<right>.+)')
async def gen_high_eq(bot: HoshinoBot, ev: CQEvent):
    uid = ev['user_id']
    gid = ev['group_id']
    left = ev['match'].group('left').strip()
    right = ev['match'].group('right').strip()

    if not _nlmt.check(uid):
        await bot.finish(ev, EXCEED_NOTICE, at_sender=True)
    if not _flmt.check(uid):
        await bot.finish(ev, f'您冲的太快了,{round(_flmt.left_time(uid))}秒后再来吧', at_sender=True)
    if len(left) > 15 or len(right) > 15:
        await bot.finish(ev, '为了图片质量，请不要多于15个字符')

    img_p = Image.open(high_eq_path)
    draw_text(img_p, left, 0)
    draw_text(img_p, right, 400)
    img = str(MessageSegment.image(pic2b64(img_p)))
    if not priv.check_priv(ev, priv.SUPERUSER):
        _flmt.start_cd(uid)
        _nlmt.increase(uid)
    await bot.send(ev, img, at_sender=True)


@sv.on_prefix('金龙')
async def gen_jl(bot: HoshinoBot, ev: CQEvent):
    uid = ev['user_id']
    gid = ev['group_id']
    args = ev.message.extract_plain_text().strip().split()

    if not _nlmt.check(uid):
        await bot.finish(ev, EXCEED_NOTICE, at_sender=True)
    if not _flmt.check(uid):
        await bot.finish(ev, f'您冲的太快了,{round(_flmt.left_time(uid))}秒后再来吧', at_sender=True)
    if args[0] == '盘旋':
        if len(args) != 4:
            await bot.finish(ev, f"金龙{args[0]}需要三个参数")
        else: url = await get_jl(args[0], args[1], args[2], args[3])
    elif args[0] == '飞升':
        if len(args) != 4:
            await bot.finish(ev, f"金龙{args[0]}需要三个参数")
        else: url = await get_jl(args[0], args[1], args[2], args[3])
    elif args[0] == '酷炫':
        if len(args) != 3:
            await bot.finish(ev, f"金龙{args[0]}需要两个参数")
        else: url = await get_jl(args[0], args[1], None, args[2])
    else: return
    
    try:
        img = str(MessageSegment.image(url))
        if not priv.check_priv(ev, priv.SUPERUSER):
            _flmt.start_cd(uid)
            _nlmt.increase(uid)
        await bot.send(ev, img, at_sender=True)
    except:
        bot.send(ev, '无法生成图片')


@sv.on_keyword(('接头霸王', '接头'))
async def concat_head(bot: HoshinoBot, ev: CQEvent):
    uid = ev['user_id']
    gid = ev['group_id']
    msg = ev.message.extract_plain_text().strip()

    if not _nlmt.check(uid):
        await bot.finish(ev, EXCEED_NOTICE, at_sender=True)
    if not _flmt.check(uid):
        await bot.finish(ev, f'您冲的太快了,{round(_flmt.left_time(uid))}秒后再来吧', at_sender=True)

    if (img := await get_image(bot, ev)) is not None:
        if '三次元' in msg or 'real' in msg:
            catimg = await concat_head_real_(img)
        else:
            catimg = await concat_head_(img)
        if catimg is not None:
            catimg = str(MessageSegment.image(pic2b64(catimg)))
            await bot.send(ev, catimg, at_sender=True)
        else:
            fail_pic = Image.open(os.path.join(os.path.dirname(__file__), 'images/head/接头失败.png'))
            await bot.send(ev, '三次元图片试试三次元接头？' + MessageSegment.image(f'file://{fail_pic}'), at_sender=True)
    else:
        await bot.send(ev, '未检测到图片信息', at_sender=True)


img = []
send_times = 0
@sv.on_command('hide_image', only_to_me=True, aliases=['隐藏图片'])
async def hide_image(session: CommandSession):
    global img
    global send_times
    await session.aget('', prompt='发送要上传的图片,暂不支持gif')
    image = await save_img(get_all_img_url(session.ctx))
    if image:
        img.extend(image)
    else:
        send_times += 1
    if send_times >= 3:
        await session.send('过多次未发送图片，已自动停止')
        img = []
        send_times = 0
        return
    if len(img) == 0:
        session.pause('请上传第一张图片')
    elif len(img) == 1:
        session.pause('请上传第二张图片')
    elif len(img) == 2:
        await session.send('正在合成图片，请稍后')
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor()
        res_img = await loop.run_in_executor(executor, make_hide_image, img[0], img[1])
        msg = str(MessageSegment.image(pic2b64(res_img)))
        img = []
        await session.finish(msg)
