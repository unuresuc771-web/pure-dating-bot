import os
import sys
import math
import random
from PIL import Image, ImageDraw, ImageFont

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MALE_DIR = os.path.join(BASE_DIR, "assets", "avatars", "male")
FEMALE_DIR = os.path.join(BASE_DIR, "assets", "avatars", "female")

os.makedirs(MALE_DIR, exist_ok=True)
os.makedirs(FEMALE_DIR, exist_ok=True)

# 20 цветовых палитр для мужчин (глубокие, стильные, киберпанк / неон / ночные тона)
MALE_PALETTES = [
    ((15, 23, 42), (30, 41, 59), (56, 189, 248)),     # Сланцево-голубой
    ((10, 10, 18), (30, 27, 75), (129, 140, 248)),    # Индиго
    ((17, 24, 39), (31, 41, 55), (244, 63, 94)),      # Темно-рубиновый
    ((3, 7, 18), (17, 24, 39), (16, 185, 129)),       # Изумрудный неон
    ((20, 10, 30), (50, 15, 60), (236, 72, 153)),     # Киберпанк фуксия
    ((15, 15, 15), (38, 38, 38), (245, 158, 11)),     # Золотистый янтарь
    ((8, 20, 30), (12, 45, 60), (6, 182, 212)),       # Бирюзовый
    ((20, 5, 25), (45, 10, 55), (168, 85, 247)),      # Пурпурный
    ((12, 18, 12), (24, 40, 24), (34, 197, 94)),      # Лесной неон
    ((25, 15, 10), (55, 30, 15), (249, 115, 22)),     # Огненный
    ((5, 15, 25), (15, 35, 60), (96, 165, 250)),      # Лазурный
    ((18, 18, 24), (35, 35, 48), (226, 232, 240)),    # Платиновый
    ((24, 10, 15), (50, 18, 28), (251, 113, 133)),    # Коралловый
    ((10, 20, 20), (20, 45, 45), (45, 212, 191)),     # Мятный
    ((25, 20, 5), (55, 45, 10), (234, 179, 8)),       # Солнечный
    ((14, 10, 30), (32, 20, 65), (192, 132, 252)),    # Лавандовый
    ((15, 25, 20), (28, 55, 40), (52, 211, 153)),     # Нефритовый
    ((28, 12, 20), (60, 25, 42), (244, 114, 182)),    # Розовый кварц
    ((10, 14, 26), (22, 32, 58), (147, 197, 253)),    # Ледяной
    ((20, 20, 20), (45, 45, 45), (255, 255, 255))     # Монохром
]

# 20 цветовых палитр для девушек (чувственные, яркие, закатные, неоновые)
FEMALE_PALETTES = [
    ((26, 10, 30), (60, 20, 70), (244, 114, 182)),    # Нежная малина
    ((20, 5, 20), (55, 12, 45), (251, 113, 133)),     # Рубин и роза
    ((15, 10, 25), (40, 20, 65), (192, 132, 252)),    # Лиловый
    ((25, 10, 15), (65, 25, 30), (251, 146, 60)),     # Закатный персик
    ((10, 15, 30), (25, 35, 70), (56, 189, 248)),     # Небесный сапфир
    ((20, 15, 5), (55, 35, 12), (250, 204, 21)),      # Теплый мед
    ((8, 25, 25), (20, 55, 55), (45, 212, 191)),      # Морская волна
    ((30, 8, 20), (70, 15, 40), (244, 63, 94)),       # Страстный алый
    ((18, 10, 32), (45, 22, 75), (167, 139, 250)),    # Глубокий аметист
    ((24, 12, 10), (58, 28, 20), (248, 113, 113)),    # Коралл
    ((12, 20, 18), (28, 50, 42), (52, 211, 153)),     # Изумрудная мята
    ((28, 18, 25), (62, 38, 54), (244, 114, 182)),    # Пудровый
    ((10, 10, 25), (25, 25, 60), (129, 140, 248)),    # Сиреневый неон
    ((22, 15, 30), (52, 32, 68), (216, 180, 254)),    # Орхидея
    ((30, 12, 12), (72, 26, 26), (252, 165, 165)),    # Нежный коралл
    ((15, 22, 30), (32, 50, 70), (125, 211, 252)),    # Лазурная бирюза
    ((25, 14, 22), (60, 30, 50), (249, 168, 212)),    # Цветущая сакура
    ((20, 18, 10), (48, 42, 22), (253, 224, 71)),     # Лунное золото
    ((15, 12, 28), (38, 28, 65), (147, 51, 234)),     # Фиолетовый
    ((20, 20, 26), (44, 44, 58), (241, 245, 249))     # Серебряный шелк
]

def draw_avatar(index: int, gender: str, palette, output_path: str):
    width, height = 600, 600
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    bg_top, bg_bottom, accent = palette

    # 1. Плавный радиально-линейный градиент фона
    for y in range(height):
        ratio = y / height
        r = int(bg_top[0] * (1 - ratio) + bg_bottom[0] * ratio)
        g = int(bg_top[1] * (1 - ratio) + bg_bottom[1] * ratio)
        b = int(bg_top[2] * (1 - ratio) + bg_bottom[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 2. Неоновые круги / аура на фоне
    center_x, center_y = width // 2, height // 2 - 30
    for rad in range(180, 70, -10):
        alpha_factor = (180 - rad) / 110
        circle_color = (
            int(bg_bottom[0] + (accent[0] - bg_bottom[0]) * alpha_factor * 0.45),
            int(bg_bottom[1] + (accent[1] - bg_bottom[1]) * alpha_factor * 0.45),
            int(bg_bottom[2] + (accent[2] - bg_bottom[2]) * alpha_factor * 0.45)
        )
        draw.ellipse(
            [center_x - rad, center_y - rad, center_x + rad, center_y + rad],
            fill=circle_color
        )

    # 3. Элегантный силуэт инкогнито (голова и плечи)
    head_radius = 85
    head_cy = center_y + 10

    # Плечи (полуовал)
    shoulders_top = head_cy + 75
    draw.ellipse(
        [center_x - 170, shoulders_top, center_x + 170, height + 100],
        fill=(10, 10, 15)
    )

    # Шея
    draw.rectangle(
        [center_x - 32, head_cy + 40, center_x + 32, shoulders_top + 30],
        fill=(10, 10, 15)
    )

    # Голова
    draw.ellipse(
        [center_x - head_radius, head_cy - head_radius, center_x + head_radius, head_cy + head_radius],
        fill=(10, 10, 15)
    )

    # 4. Стильные детали Pure (маска / очки / взгляд / неон)
    if gender == "male":
        # Неоновые геометрические очки / линия взгляда
        eye_y = head_cy - 10
        draw.rounded_rectangle(
            [center_x - 55, eye_y - 12, center_x + 55, eye_y + 12],
            radius=6,
            fill=accent
        )
        # Блик
        draw.line([center_x - 45, eye_y - 4, center_x - 10, eye_y - 4], fill=(255, 255, 255), width=3)
    else:
        # Утонченная чувственная маска / линия
        eye_y = head_cy - 12
        # Контур кошачьих глаз / элегантной маски
        points = [
            (center_x - 65, eye_y - 5),
            (center_x - 20, eye_y + 8),
            (center_x, eye_y + 2),
            (center_x + 20, eye_y + 8),
            (center_x + 65, eye_y - 5),
            (center_x + 40, eye_y - 14),
            (center_x, eye_y - 8),
            (center_x - 40, eye_y - 14)
        ]
        draw.polygon(points, fill=accent)
        draw.line([center_x - 50, eye_y - 6, center_x - 25, eye_y - 2], fill=(255, 255, 255), width=2)
        draw.line([center_x + 25, eye_y - 2, center_x + 50, eye_y - 6], fill=(255, 255, 255), width=2)

    # 5. Тонкая акцентная неоновая рамка
    draw.rounded_rectangle([15, 15, width - 15, height - 15], radius=24, outline=accent, width=3)

    # 6. Лаконичная подпись PURE внизу
    label = f"PURE #{index:02d}"
    draw.text((width // 2 - 38, height - 55), label, fill=accent)

    img.save(output_path, "JPEG", quality=95)

def main():
    print("🎨 Generating 20 Male and 20 Female Anonymous Avatars...")
    for i in range(1, 21):
        male_file = os.path.join(MALE_DIR, f"male_{i:02d}.jpg")
        draw_avatar(i, "man", MALE_PALETTES[i-1], male_file)

        female_file = os.path.join(FEMALE_DIR, f"female_{i:02d}.jpg")
        draw_avatar(i, "woman", FEMALE_PALETTES[i-1], female_file)

    print("✅ All 40 anonymous avatar images created successfully in assets/avatars/!")

if __name__ == "__main__":
    main()
