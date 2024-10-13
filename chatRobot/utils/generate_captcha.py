import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

str_all = string.digits + string.ascii_letters
width = 170
height = 40


def random_color():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


def generate_str_captcha():
    # 生成200 X 40的白色图片
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    # 创建画布
    draw = ImageDraw.Draw(img)
    # 随机画点
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), random_color())
    # 随机画线
    for _ in range(10):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line((x1, y1, x2, y2), random_color(), width=5)
    # 生成字体对象
    font = ImageFont.truetype(font="chatRobot/static/font/firasansblack-ox6o.ttf", size=30)
    codes = []
    for _ in range(4):
        code = random.choice(str_all)
        codes.append(code)
        draw.text((33 * (_ + 1), 3), code, (0, 0, 0), font=font)
    with BytesIO() as f:
        img.save(f, "PNG")
        return f.getvalue(), "".join(codes).lower()