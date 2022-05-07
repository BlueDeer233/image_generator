# 生草图片生成器

适用hoshino，集成 [5000choyen](https://github.com/pcrbot/5000choyen)、[千雪bot](https://github.com/Diving-Fish/Chiyuki-Bot)、[接头](https://github.com/pcrbot/plugins-for-Hoshino/tree/master/shebot/conhead)、[幻影坦克](https://github.com/kosakarin/hide_img)图片生成器和附加一些功能的图片生成器插件

## 使用方法
1. 将该项目放在HoshinoBot插件目录 `modules` 下，或者clone本项目 `git clone https://github.com/BlueDeer233/image_generator.git`  
2. pip以下依赖：`pillow` `opencv-python`  
3. 在[head_source.py](src/head_source.py) line12~13填入[百度人脸检测](https://console.bce.baidu.com/ai/#/ai/face/overview/index) apikey
4. 在`config/__bot__.py`模块列表中添加 `image_generator`  
5. 重启HoshinoBot  

## 指令
5000兆元|5000兆円|5kcy (上半句) (下半句)  
低情商 <文本> 高情商 <文本>  
金龙盘旋 <文字1> <文字2> <底部文字>  
金龙飞升 <文字1> <文字2> <底部文字>  
金龙酷炫 <文字> <底部文字>  
接头 <图片>  
real接头 <图片>  
@bot 隐藏图片  
ps：隐藏图片 发送彩图进图彩图模式
## 鸣谢

感谢 [leinlin](https://zhuanlan.zhihu.com/p/32532733) 提供的彩图幻影坦克教程  
感谢 [kosakarin](https://github.com/kosakarin/hide_img) 提供的源码支持  
感谢 [shebot](https://github.com/pcrbot/plugins-for-Hoshino) 提供的源码支持  
感谢 [Diving-Fish](https://github.com/Diving-Fish/Chiyuki-Bot) 提供的源码支持  
感谢 [pcrbot](https://github.com/pcrbot) 提供的源码支持

## License

MIT
您可以自由使用本项目的代码用于商业或非商业的用途，但必须附带 MIT 授权协议。
