import os
import sys
import math
import random
from PIL import Image, ImageDraw

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

# Психоделические контрастные двухцветные палитры в стиле Pure
PSYCHEDELIC_PALETTES = [
    ((255, 0, 128), (255, 90, 0)),    # Розовый + Неоновый оранжевый (как на лого Pure)
    ((230, 0, 160), (255, 60, 0)),    # Фуксия + Апельсин
    ((0, 255, 128), (140, 0, 255)),   # Токсичный лайм + Фиолетовый
    ((0, 230, 255), (255, 0, 90)),    # Кибер-циан + Маджента
    ((255, 230, 0), (180, 0, 255)),   # Электрический желтый + Неоновый фиолет
    ((255, 40, 0), (0, 240, 255)),    # Красный + Бирюза
    ((255, 0, 200), (0, 255, 200)),   # Неоновый розовый + Мята
    ((255, 110, 0), (120, 0, 255)),   # Оранжевый + Ультрафиолет
    ((0, 255, 60), (255, 0, 140)),    # Кислотная зелень + Фуксия
    ((255, 220, 0), (255, 0, 80)),    # Золотой + Рубин
    ((30, 144, 255), (255, 105, 180)),# Синий сапфир + Розовый
    ((255, 69, 0), (50, 205, 50)),    # Огненный + Салатовый
    ((186, 85, 211), (255, 215, 0)),  # Аметист + Золото
    ((0, 206, 209), (255, 20, 147)),  # Морской + Пылающая роза
    ((255, 99, 71), (138, 43, 226)),  # Томатный + Индиго
    ((0, 250, 154), (255, 140, 0)),   # Весенняя зелень + Темный оранжевый
    ((255, 0, 255), (255, 255, 0)),   # Чистый циан + Желтый
    ((220, 20, 60), (0, 255, 255)),   # Малиновый + Аква
    ((153, 50, 204), (255, 165, 0)),  # Баклажан + Мандарин
    ((255, 20, 147), (255, 160, 122)) # Глубокий розовый + Персик
]

def render_wavy_background(width, height, color1, color2, wave_type=0):
    img = Image.new("RGB", (width, height), color1)
    draw = ImageDraw.Draw(img)

    cx, cy = width // 2, height // 2
    step = 22

    for r in range(step, int(width * 1.2), step * 2):
        points = []
        for angle_deg in range(0, 365, 5):
            rad = math.radians(angle_deg)
            # Добавляем психоделическое искривление
            if wave_type % 3 == 0:
                dist = r + 18 * math.sin(6 * rad) + 12 * math.cos(3 * rad)
            elif wave_type % 3 == 1:
                dist = r + 24 * math.sin(4 * rad + 0.5) + 15 * math.sin(8 * rad)
            else:
                dist = r + 20 * math.cos(5 * rad) + 16 * math.sin(2 * rad)

            x = cx + dist * math.cos(rad)
            y = cy + dist * math.sin(rad)
            points.append((x, y))

        draw.polygon(points, fill=color2)

    return img

def draw_male_creature(draw, cx, cy, idx, accent):
    # Силуэт монстра Pure черного цвета
    black = (10, 5, 15)

    if idx == 1:
        # 1. Классический циклоп с крутыми рогами (как лого Pure)
        # Тело и плечи
        draw.ellipse([cx - 160, cy + 100, cx + 160, cy + 380], fill=black)
        draw.rectangle([cx - 35, cy + 60, cx + 35, cy + 120], fill=black)
        # Голова
        draw.ellipse([cx - 85, cy - 60, cx + 85, cy + 90], fill=black)
        # Острые серповидные рога вверх
        draw.polygon([(cx - 70, cy - 20), (cx - 140, cy - 140), (cx - 90, cy - 170), (cx - 45, cy - 50)], fill=black)
        draw.polygon([(cx + 70, cy - 20), (cx + 140, cy - 140), (cx + 90, cy - 170), (cx + 45, cy - 50)], fill=black)
        # Один большой циклопный глаз
        draw.ellipse([cx - 40, cy, cx + 40, cy + 35], fill=accent)
        draw.ellipse([cx - 15, cy + 8, cx + 15, cy + 27], fill=black)

    elif idx == 2:
        # 2. Рогатый демон с козлиными витыми рогами и зубастой ухмылкой
        draw.ellipse([cx - 150, cy + 110, cx + 150, cy + 380], fill=black)
        draw.ellipse([cx - 90, cy - 50, cx + 90, cy + 100], fill=black)
        # Витые широкие рога
        draw.polygon([(cx - 75, cy - 30), (cx - 160, cy - 80), (cx - 130, cy - 160), (cx - 50, cy - 60)], fill=black)
        draw.polygon([(cx + 75, cy - 30), (cx + 160, cy - 80), (cx + 130, cy - 160), (cx + 50, cy - 60)], fill=black)
        # Два светящихся узких глаза
        draw.polygon([(cx - 60, cy + 5), (cx - 20, cy + 15), (cx - 50, cy + 20)], fill=accent)
        draw.polygon([(cx + 60, cy + 5), (cx + 20, cy + 15), (cx + 50, cy + 20)], fill=accent)
        # Острые клыки
        draw.polygon([(cx - 20, cy + 60), (cx - 10, cy + 75), (cx, cy + 60), (cx + 10, cy + 75), (cx + 20, cy + 60)], fill=(255, 255, 255))

    elif idx == 3:
        # 3. Сумасшедший заяц-демон с длинными ушами и спиральными глазами
        draw.ellipse([cx - 140, cy + 120, cx + 140, cy + 380], fill=black)
        draw.ellipse([cx - 80, cy - 40, cx + 80, cy + 100], fill=black)
        # Длинные кривые уши
        draw.polygon([(cx - 60, cy - 30), (cx - 110, cy - 200), (cx - 40, cy - 190), (cx - 30, cy - 40)], fill=black)
        draw.polygon([(cx + 60, cy - 30), (cx + 110, cy - 200), (cx + 40, cy - 190), (cx + 30, cy - 40)], fill=black)
        # Глаза спирали
        draw.ellipse([cx - 55, cy + 10, cx - 15, cy + 50], fill=accent)
        draw.ellipse([cx + 15, cy + 10, cx + 55, cy + 50], fill=accent)
        draw.ellipse([cx - 42, cy + 22, cx - 28, cy + 38], fill=black)
        draw.ellipse([cx + 28, cy + 22, cx + 42, cy + 38], fill=black)

    elif idx == 4:
        # 4. Пришелец с тремя глазами и щупальцами на голове
        draw.ellipse([cx - 170, cy + 100, cx + 170, cy + 380], fill=black)
        # Овальная вытянутая голова
        draw.ellipse([cx - 105, cy - 90, cx + 105, cy + 90], fill=black)
        # Щупальца/антенны
        draw.ellipse([cx - 120, cy - 130, cx - 70, cy - 80], fill=black)
        draw.ellipse([cx + 70, cy - 130, cx + 120, cy - 80], fill=black)
        # 3 глаза
        draw.ellipse([cx - 60, cy - 10, cx - 25, cy + 25], fill=accent)
        draw.ellipse([cx + 25, cy - 10, cx + 60, cy + 25], fill=accent)
        draw.ellipse([cx - 20, cy - 50, cx + 20, cy - 15], fill=accent)

    elif idx == 5:
        # 5. Кибер-ниндзя в маске с неоновой полосой и шипами
        draw.ellipse([cx - 150, cy + 90, cx + 150, cy + 380], fill=black)
        draw.rectangle([cx - 75, cy - 60, cx + 75, cy + 80], fill=black)
        # Шипы на плечах
        draw.polygon([(cx - 160, cy + 90), (cx - 140, cy + 40), (cx - 120, cy + 90)], fill=black)
        draw.polygon([(cx + 160, cy + 90), (cx + 140, cy + 40), (cx + 120, cy + 90)], fill=black)
        # Неоновый визор
        draw.rounded_rectangle([cx - 60, cy - 10, cx + 60, cy + 15], radius=6, fill=accent)
        draw.line([cx - 50, cy + 2, cx + 50, cy + 2], fill=(255, 255, 255), width=3)

    elif idx == 6:
        # 6. Череп-демон с горящими глазницами
        draw.ellipse([cx - 160, cy + 100, cx + 160, cy + 380], fill=black)
        draw.ellipse([cx - 85, cy - 70, cx + 85, cy + 70], fill=black)
        draw.rectangle([cx - 45, cy + 50, cx + 45, cy + 95], fill=black)
        # Глазницы
        draw.ellipse([cx - 55, cy - 15, cx - 15, cy + 25], fill=accent)
        draw.ellipse([cx + 15, cy - 15, cx + 55, cy + 25], fill=accent)
        # Нос треугольник
        draw.polygon([(cx, cy + 30), (cx - 12, cy + 48), (cx + 12, cy + 48)], fill=accent)

    elif idx == 7:
        # 7. Минотавр с кольцом в носу и массивными рогами в стороны
        draw.ellipse([cx - 180, cy + 90, cx + 180, cy + 380], fill=black)
        draw.ellipse([cx - 95, cy - 50, cx + 95, cy + 95], fill=black)
        # Мощные рога полумесяцем
        draw.polygon([(cx - 80, cy), (cx - 175, cy - 40), (cx - 160, cy - 120), (cx - 65, cy - 40)], fill=black)
        draw.polygon([(cx + 80, cy), (cx + 175, cy - 40), (cx + 160, cy - 120), (cx + 65, cy - 40)], fill=black)
        # Глаза
        draw.ellipse([cx - 55, cy + 5, cx - 25, cy + 30], fill=accent)
        draw.ellipse([cx + 25, cy + 5, cx + 55, cy + 30], fill=accent)
        # Септум кольцо
        draw.ellipse([cx - 20, cy + 65, cx + 20, cy + 105], outline=accent, width=6)

    elif idx == 8:
        # 8. Панк с ирокезом и шипами
        draw.ellipse([cx - 150, cy + 100, cx + 150, cy + 380], fill=black)
        draw.ellipse([cx - 80, cy - 50, cx + 80, cy + 90], fill=black)
        # Ирокез
        draw.polygon([(cx - 25, cy - 50), (cx - 40, cy - 180), (cx, cy - 195), (cx + 40, cy - 180), (cx + 25, cy - 50)], fill=black)
        # Глаза косые
        draw.line([cx - 55, cy + 10, cx - 15, cy + 25], fill=accent, width=8)
        draw.line([cx + 55, cy + 10, cx + 15, cy + 25], fill=accent, width=8)

    elif idx == 9:
        # 9. Кот-демон с острыми ушами и светящимся оскалом
        draw.ellipse([cx - 150, cy + 100, cx + 150, cy + 380], fill=black)
        draw.ellipse([cx - 85, cy - 50, cx + 85, cy + 90], fill=black)
        # Острые треугольные уши
        draw.polygon([(cx - 85, cy - 20), (cx - 95, cy - 140), (cx - 25, cy - 50)], fill=black)
        draw.polygon([(cx + 85, cy - 20), (cx + 95, cy - 140), (cx + 25, cy - 50)], fill=black)
        # Кошачьи щелевидные зрачки
        draw.ellipse([cx - 55, cy + 10, cx - 20, cy + 35], fill=accent)
        draw.ellipse([cx + 20, cy + 10, cx + 55, cy + 35], fill=accent)
        draw.line([cx - 37, cy + 10, cx - 37, cy + 35], fill=black, width=4)
        draw.line([cx + 37, cy + 10, cx + 37, cy + 35], fill=black, width=4)

    elif idx == 10:
        # 10. Чеширский монстр с гигантской улыбкой
        draw.ellipse([cx - 160, cy + 110, cx + 160, cy + 380], fill=black)
        draw.ellipse([cx - 90, cy - 40, cx + 90, cy + 100], fill=black)
        # Глаза полумесяцы
        draw.arc([cx - 60, cy - 10, cx - 20, cy + 30], 180, 360, fill=accent, width=6)
        draw.arc([cx + 20, cy - 10, cx + 60, cy + 30], 180, 360, fill=accent, width=6)
        # Огромная светящаяся улыбка с зубьями
        draw.arc([cx - 70, cy + 30, cx + 70, cy + 85], 0, 180, fill=accent, width=6)
        draw.line([cx - 40, cy + 45, cx - 40, cy + 65], fill=accent, width=3)
        draw.line([cx, cy + 50, cx, cy + 72], fill=accent, width=3)
        draw.line([cx + 40, cy + 45, cx + 40, cy + 65], fill=accent, width=3)

    elif idx == 11:
        # 11. Летучая мышь Носферату
        draw.ellipse([cx - 150, cy + 100, cx + 150, cy + 380], fill=black)
        draw.ellipse([cx - 80, cy - 40, cx + 80, cy + 90], fill=black)
        # Крылатые уши
        draw.polygon([(cx - 70, cy - 20), (cx - 130, cy - 130), (cx - 60, cy - 100), (cx - 20, cy - 40)], fill=black)
        draw.polygon([(cx + 70, cy - 20), (cx + 130, cy - 130), (cx + 60, cy - 100), (cx + 20, cy - 40)], fill=black)
        # Красные круглые глаза
        draw.ellipse([cx - 45, cy + 10, cx - 15, cy + 40], fill=accent)
        draw.ellipse([cx + 15, cy + 10, cx + 45, cy + 40], fill=accent)
        # Клыки вниз
        draw.polygon([(cx - 20, cy + 60), (cx - 12, cy + 80), (cx - 5, cy + 60)], fill=(255, 255, 255))
        draw.polygon([(cx + 5, cy + 60), (cx + 12, cy + 80), (cx + 20, cy + 60)], fill=(255, 255, 255))

    elif idx == 12:
        # 12. Кубистический Пикассо-демон (асимметричные глаза и губы)
        draw.ellipse([cx - 150, cy + 100, cx + 150, cy + 380], fill=black)
        draw.polygon([(cx - 80, cy - 50), (cx + 70, cy - 80), (cx + 90, cy + 60), (cx - 70, cy + 90)], fill=black)
        # Один глаз круглый высоко, другой миндалевидный низко
        draw.ellipse([cx - 55, cy - 35, cx - 15, cy + 5], fill=accent)
        draw.ellipse([cx + 15, cy + 10, cx + 65, cy + 40], fill=accent)
        # Кривой нос линия
        draw.line([cx - 10, cy - 10, cx + 15, cy + 30], fill=accent, width=4)

    elif idx == 13:
        # 13. Капюшон с горящими углями глаз
        draw.polygon([(cx - 170, cy + 120), (cx - 110, cy - 110), (cx, cy - 170), (cx + 110, cy - 110), (cx + 170, cy + 120)], fill=black)
        draw.ellipse([cx - 65, cy - 10, cx + 65, cy + 70], fill=(0, 0, 0))
        # Горящие глаза в темноте
        draw.ellipse([cx - 40, cy + 15, cx - 10, cy + 35], fill=accent)
        draw.ellipse([cx + 10, cy + 15, cx + 40, cy + 35], fill=accent)

    elif idx == 14:
        # 14. Четырехглазый мутант
        draw.ellipse([cx - 160, cy + 100, cx + 160, cy + 380], fill=black)
        draw.ellipse([cx - 90, cy - 60, cx + 90, cy + 90], fill=black)
        # 4 глаза в 2 ряда
        draw.ellipse([cx - 55, cy - 25, cx - 20, cy + 5], fill=accent)
        draw.ellipse([cx + 20, cy - 25, cx + 55, cy + 5], fill=accent)
        draw.ellipse([cx - 50, cy + 15, cx - 15, cy + 45], fill=accent)
        draw.ellipse([cx + 15, cy + 15, cx + 50, cy + 45], fill=accent)

    elif idx == 15:
        # 15. Космический шлем с рогами
        draw.ellipse([cx - 150, cy + 100, cx + 150, cy + 380], fill=black)
        draw.ellipse([cx - 95, cy - 70, cx + 95, cy + 80], fill=black)
        # Антенны рога
        draw.line([cx - 70, cy - 50, cx - 130, cy - 140], fill=accent, width=8)
        draw.line([cx + 70, cy - 50, cx + 130, cy - 140], fill=accent, width=8)
        draw.ellipse([cx - 140, cy - 150, cx - 120, cy - 130], fill=accent)
        draw.ellipse([cx + 120, cy - 150, cx + 140, cy - 130], fill=accent)
        # Отражение на стекле
        draw.ellipse([cx - 60, cy - 20, cx + 60, cy + 40], fill=accent)
        draw.ellipse([cx - 50, cy - 15, cx + 10, cy + 10], fill=(255, 255, 255))

    elif idx == 16:
        # 16. БДСМ кожаная маска на молнии
        draw.ellipse([cx - 150, cy + 100, cx + 150, cy + 380], fill=black)
        draw.ellipse([cx - 85, cy - 60, cx + 85, cy + 85], fill=black)
        # Молния на рту
        draw.line([cx - 45, cy + 55, cx + 45, cy + 55], fill=accent, width=8)
        for zx in range(cx - 40, cx + 45, 10):
            draw.line([zx, cy + 50, zx, cy + 60], fill=(255, 255, 255), width=2)
        # Глаза прорези
        draw.polygon([(cx - 55, cy + 5), (cx - 15, cy + 5), (cx - 35, cy + 20)], fill=accent)
        draw.polygon([(cx + 15, cy + 5), (cx + 55, cy + 5), (cx + 35, cy + 20)], fill=accent)

    elif idx == 17:
        # 17. Огненный дракон с гребнем
        draw.ellipse([cx - 160, cy + 100, cx + 160, cy + 380], fill=black)
        draw.ellipse([cx - 85, cy - 50, cx + 85, cy + 90], fill=black)
        # Гребень из 4 зубьев на голове
        for gx, gy in [(-60, -90), (-20, -130), (20, -130), (60, -90)]:
            draw.polygon([(gx - 15, cy - 40), (gx, gy), (gx + 15, cy - 40)], fill=black)
        # Глаза рептилии
        draw.ellipse([cx - 55, cy + 5, cx - 20, cy + 35], fill=accent)
        draw.ellipse([cx + 20, cy + 5, cx + 55, cy + 35], fill=accent)
        draw.line([cx - 37, cy + 5, cx - 37, cy + 35], fill=black, width=5)
        draw.line([cx + 37, cy + 5, cx + 37, cy + 35], fill=black, width=5)

    elif idx == 18:
        # 18. Безумный шут/джокер с рожками колпака
        draw.ellipse([cx - 150, cy + 100, cx + 150, cy + 380], fill=black)
        draw.ellipse([cx - 80, cy - 40, cx + 80, cy + 90], fill=black)
        # Колпак шута с бубенцами
        draw.polygon([(cx - 60, cy - 30), (cx - 140, cy - 100), (cx - 30, cy - 50)], fill=black)
        draw.polygon([(cx + 60, cy - 30), (cx + 140, cy - 100), (cx + 30, cy - 50)], fill=black)
        draw.ellipse([cx - 150, cy - 110, cx - 130, cy - 90], fill=accent)
        draw.ellipse([cx + 130, cy - 110, cx + 150, cy - 90], fill=accent)
        # Зловещая улыбка
        draw.arc([cx - 50, cy + 25, cx + 50, cy + 75], 0, 180, fill=accent, width=5)

    elif idx == 19:
        # 19. Теневой голем с расколотым лицом
        draw.ellipse([cx - 160, cy + 100, cx + 160, cy + 380], fill=black)
        draw.polygon([(cx - 85, cy - 50), (cx + 85, cy - 50), (cx + 70, cy + 90), (cx - 70, cy + 90)], fill=black)
        # Светящаяся трещина через все лицо
        crack = [(cx - 20, cy - 60), (cx - 5, cy - 20), (cx - 25, cy + 10), (cx + 5, cy + 40), (cx - 10, cy + 90)]
        for i in range(len(crack) - 1):
            draw.line([crack[i], crack[i+1]], fill=accent, width=6)
        # Глаз один
        draw.ellipse([cx + 25, cy - 5, cx + 55, cy + 20], fill=accent)

    else:
        # 20. Сердце-демон с рогами и стрелой
        draw.ellipse([cx - 150, cy + 110, cx + 150, cy + 380], fill=black)
        # Сердце голова
        draw.ellipse([cx - 80, cy - 60, cx, cy + 20], fill=black)
        draw.ellipse([cx, cy - 60, cx + 80, cy + 20], fill=black)
        draw.polygon([(cx - 75, cy - 10), (cx, cy + 90), (cx + 75, cy - 10)], fill=black)
        # Рожки
        draw.polygon([(cx - 60, cy - 40), (cx - 95, cy - 110), (cx - 40, cy - 60)], fill=black)
        draw.polygon([(cx + 60, cy - 40), (cx + 95, cy - 110), (cx + 40, cy - 60)], fill=black)
        # Око страсти
        draw.ellipse([cx - 30, cy + 5, cx + 30, cy + 40], fill=accent)
        draw.ellipse([cx - 10, cy + 15, cx + 10, cy + 30], fill=(255, 255, 255))

    # Рамка вокруг
    draw.rounded_rectangle([15, 15, 585, 585], radius=24, outline=black, width=8)

def draw_female_creature(draw, cx, cy, idx, accent):
    # Силуэт монстра Pure женского пола (чувственные, роковые, бестии, сирены, ведьмы)
    black = (10, 5, 15)

    if idx == 1:
        # 1. Чертовка с длинными изогнутыми рогами и соблазнительными губами
        draw.ellipse([cx - 140, cy + 100, cx + 140, cy + 380], fill=black)
        draw.ellipse([cx - 75, cy - 50, cx + 75, cy + 85], fill=black)
        # Тонкие изогнутые рога
        draw.polygon([(cx - 60, cy - 20), (cx - 120, cy - 150), (cx - 80, cy - 170), (cx - 40, cy - 45)], fill=black)
        draw.polygon([(cx + 60, cy - 20), (cx + 120, cy - 150), (cx + 80, cy - 170), (cx + 40, cy - 45)], fill=black)
        # Кошачьи миндалевидные глаза
        draw.polygon([(cx - 65, cy + 5), (cx - 20, cy + 15), (cx - 50, cy + 25)], fill=accent)
        draw.polygon([(cx + 65, cy + 5), (cx + 20, cy + 15), (cx + 50, cy + 25)], fill=accent)
        # Яркие губы
        draw.ellipse([cx - 25, cy + 55, cx + 25, cy + 75], fill=accent)

    elif idx == 2:
        # 2. Суккуб с крылышками у висков
        draw.ellipse([cx - 140, cy + 100, cx + 140, cy + 380], fill=black)
        draw.ellipse([cx - 75, cy - 50, cx + 75, cy + 85], fill=black)
        # Крылья летучей мыши по бокам головы
        draw.polygon([(cx - 70, cy), (cx - 160, cy - 80), (cx - 120, cy - 120), (cx - 50, cy - 30)], fill=black)
        draw.polygon([(cx + 70, cy), (cx + 160, cy - 80), (cx + 120, cy - 120), (cx + 50, cy - 30)], fill=black)
        # Третий глаз на лбу
        draw.ellipse([cx - 20, cy - 35, cx + 20, cy - 5], fill=accent)
        draw.ellipse([cx - 50, cy + 15, cx - 20, cy + 35], fill=accent)
        draw.ellipse([cx + 20, cy + 15, cx + 50, cy + 35], fill=accent)

    elif idx == 3:
        # 3. Дикая кошка / Бастет с длинными ушами
        draw.ellipse([cx - 130, cy + 110, cx + 130, cy + 380], fill=black)
        draw.ellipse([cx - 70, cy - 40, cx + 70, cy + 85], fill=black)
        # Высокие кошачьи уши
        draw.polygon([(cx - 70, cy - 20), (cx - 80, cy - 160), (cx - 20, cy - 50)], fill=black)
        draw.polygon([(cx + 70, cy - 20), (cx + 80, cy - 160), (cx + 20, cy - 50)], fill=black)
        # Усики
        draw.line([cx - 40, cy + 45, cx - 110, cy + 35], fill=accent, width=3)
        draw.line([cx - 40, cy + 55, cx - 105, cy + 60], fill=accent, width=3)
        draw.line([cx + 40, cy + 45, cx + 110, cy + 35], fill=accent, width=3)
        draw.line([cx + 40, cy + 55, cx + 105, cy + 60], fill=accent, width=3)
        # Глаза
        draw.ellipse([cx - 50, cy + 10, cx - 15, cy + 35], fill=accent)
        draw.ellipse([cx + 15, cy + 10, cx + 50, cy + 35], fill=accent)

    elif idx == 4:
        # 4. Медуза со змеями вместо волос
        draw.ellipse([cx - 140, cy + 110, cx + 140, cy + 380], fill=black)
        draw.ellipse([cx - 75, cy - 40, cx + 75, cy + 85], fill=black)
        # Змеи вокруг головы
        for sx, sy in [(-90, -110), (-40, -150), (40, -150), (90, -110), (-130, -50), (130, -50)]:
            draw.line([cx, cy - 20, cx + sx, cy + sy], fill=black, width=22)
            draw.ellipse([cx + sx - 15, cy + sy - 15, cx + sx + 15, cy + sy + 15], fill=accent)
        # Гипнотический взгляд
        draw.ellipse([cx - 45, cy + 10, cx - 15, cy + 40], fill=accent)
        draw.ellipse([cx + 15, cy + 10, cx + 45, cy + 40], fill=accent)

    elif idx == 5:
        # 5. Циклопка в стиле Pure с огромным глазом и сережкой
        draw.ellipse([cx - 140, cy + 100, cx + 140, cy + 380], fill=black)
        draw.ellipse([cx - 75, cy - 50, cx + 75, cy + 85], fill=black)
        # Рожки кокетливые маленькие
        draw.polygon([(cx - 50, cy - 40), (cx - 70, cy - 100), (cx - 30, cy - 55)], fill=black)
        draw.polygon([(cx + 50, cy - 40), (cx + 70, cy - 100), (cx + 30, cy - 55)], fill=black)
        # Огромный глаз с пышными ресницами
        draw.ellipse([cx - 45, cy - 10, cx + 45, cy + 35], fill=accent)
        draw.ellipse([cx - 15, cy, cx + 15, cy + 25], fill=black)
        # Ресницы
        for rx, ry in [(-40, -25), (-20, -35), (0, -40), (20, -35), (40, -25)]:
            draw.line([cx + rx // 2, cy - 5, cx + rx, cy + ry], fill=black, width=4)

    elif idx == 6:
        # 6. Паучья королева (6 глаз)
        draw.ellipse([cx - 140, cy + 100, cx + 140, cy + 380], fill=black)
        draw.ellipse([cx - 75, cy - 50, cx + 75, cy + 85], fill=black)
        # 6 светящихся рубиновых глаз
        draw.ellipse([cx - 50, cy - 15, cx - 25, cy + 10], fill=accent)
        draw.ellipse([cx + 25, cy - 15, cx + 50, cy + 10], fill=accent)
        draw.ellipse([cx - 20, cy - 35, cx - 5, cy - 20], fill=accent)
        draw.ellipse([cx + 5, cy - 35, cx + 20, cy - 20], fill=accent)
        draw.ellipse([cx - 45, cy + 20, cx - 25, cy + 40], fill=accent)
        draw.ellipse([cx + 25, cy + 20, cx + 50, cy + 40], fill=accent)

    elif idx == 7:
        # 7. Роковая бестия с полумесяцем на лбу
        draw.ellipse([cx - 130, cy + 110, cx + 130, cy + 380], fill=black)
        draw.ellipse([cx - 70, cy - 40, cx + 70, cy + 85], fill=black)
        # Рожки
        draw.polygon([(cx - 55, cy - 30), (cx - 100, cy - 120), (cx - 35, cy - 50)], fill=black)
        draw.polygon([(cx + 55, cy - 30), (cx + 100, cy - 120), (cx + 35, cy - 50)], fill=black)
        # Полумесяц на лбу
        draw.arc([cx - 25, cy - 35, cx + 25, cy - 5], 40, 260, fill=accent, width=6)
        # Раскосые кошачьи глаза
        draw.line([cx - 55, cy + 15, cx - 15, cy + 25], fill=accent, width=6)
        draw.line([cx + 15, cy + 25, cx + 55, cy + 15], fill=accent, width=6)

    elif idx == 8:
        # 8. Кицунэ (лисица с длинной мордочкой и острыми ушками)
        draw.ellipse([cx - 140, cy + 100, cx + 140, cy + 380], fill=black)
        draw.polygon([(cx - 80, cy - 30), (cx, cy + 90), (cx + 80, cy - 30)], fill=black)
        # Большие лисьи уши
        draw.polygon([(cx - 80, cy - 20), (cx - 95, cy - 155), (cx - 25, cy - 40)], fill=black)
        draw.polygon([(cx + 80, cy - 20), (cx + 95, cy - 155), (cx + 25, cy - 40)], fill=black)
        # Хитрые раскосые глаза
        draw.polygon([(cx - 60, cy + 5), (cx - 20, cy + 15), (cx - 45, cy + 20)], fill=accent)
        draw.polygon([(cx + 60, cy + 5), (cx + 20, cy + 15), (cx + 45, cy + 20)], fill=accent)

    elif idx == 9:
        # 9. Морская сирена с короной-кораллом
        draw.ellipse([cx - 140, cy + 100, cx + 140, cy + 380], fill=black)
        draw.ellipse([cx - 75, cy - 40, cx + 75, cy + 85], fill=black)
        # Корона из 5 шипов
        for px, py in [(-60, -90), (-30, -120), (0, -140), (30, -120), (60, -90)]:
            draw.polygon([(px - 10, cy - 35), (px, py), (px + 10, cy - 35)], fill=black)
            draw.ellipse([px - 5, py - 5, px + 5, py + 5], fill=accent)
        # Глаза капли
        draw.ellipse([cx - 45, cy + 10, cx - 15, cy + 40], fill=accent)
        draw.ellipse([cx + 15, cy + 10, cx + 45, cy + 40], fill=accent)

    elif idx == 10:
        # 10. Девушка-призрак с текущей слезой
        draw.ellipse([cx - 130, cy + 110, cx + 130, cy + 380], fill=black)
        draw.ellipse([cx - 70, cy - 40, cx + 70, cy + 85], fill=black)
        # Длинные развивающиеся волосы по бокам
        draw.polygon([(cx - 70, cy - 40), (cx - 140, cy + 150), (cx - 60, cy + 80)], fill=black)
        draw.polygon([(cx + 70, cy - 40), (cx + 140, cy + 150), (cx + 60, cy + 80)], fill=black)
        # Глаза и текущая неоновая капля
        draw.ellipse([cx - 45, cy + 10, cx - 15, cy + 30], fill=accent)
        draw.ellipse([cx + 15, cy + 10, cx + 45, cy + 30], fill=accent)
        draw.line([cx - 30, cy + 30, cx - 30, cy + 70], fill=accent, width=4)

    elif idx == 11:
        # 11. Готическая кукла со швами
        draw.ellipse([cx - 140, cy + 100, cx + 140, cy + 380], fill=black)
        draw.ellipse([cx - 75, cy - 45, cx + 75, cy + 85], fill=black)
        # Два хвостика по бокам
        draw.ellipse([cx - 140, cy - 60, cx - 60, cy + 20], fill=black)
        draw.ellipse([cx + 60, cy - 60, cx + 140, cy + 20], fill=black)
        # Глаза крестики
        draw.line([cx - 50, cy + 5, cx - 20, cy + 35], fill=accent, width=5)
        draw.line([cx - 20, cy + 5, cx - 50, cy + 35], fill=accent, width=5)
        draw.line([cx + 20, cy + 5, cx + 50, cy + 35], fill=accent, width=5)
        draw.line([cx + 50, cy + 5, cx + 20, cy + 35], fill=accent, width=5)

    elif idx == 12:
        # 12. Черная дыра / Глаз в треугольнике
        draw.ellipse([cx - 140, cy + 100, cx + 140, cy + 380], fill=black)
        # Треугольная голова
        draw.polygon([(cx - 95, cy + 80), (cx, cy - 100), (cx + 95, cy + 80)], fill=black)
        # Глаз в центре
        draw.ellipse([cx - 40, cy - 10, cx + 40, cy + 40], fill=accent)
        draw.ellipse([cx - 15, cy + 5, cx + 15, cy + 25], fill=black)

    elif idx == 13:
        # 13. Инопланетянка с длинной шеей и антеннами
        draw.ellipse([cx - 120, cy + 140, cx + 120, cy + 380], fill=black)
        draw.rectangle([cx - 20, cy + 50, cx + 20, cy + 140], fill=black)
        draw.ellipse([cx - 65, cy - 50, cx + 65, cy + 60], fill=black)
        # Две длинные антенны с шариками
        draw.line([cx - 40, cy - 40, cx - 80, cy - 150], fill=black, width=8)
        draw.line([cx + 40, cy - 40, cx + 80, cy - 150], fill=black, width=8)
        draw.ellipse([cx - 95, cy - 165, cx - 65, cy - 135], fill=accent)
        draw.ellipse([cx + 65, cy - 165, cx + 95, cy - 135], fill=accent)
        # Миндалевидные огромные глаза
        draw.ellipse([cx - 50, cy - 10, cx - 15, cy + 25], fill=accent)
        draw.ellipse([cx + 15, cy - 10, cx + 50, cy + 25], fill=accent)

    elif idx == 14:
        # 14. Мотылек / бабочка с крыльями на голове
        draw.ellipse([cx - 130, cy + 100, cx + 130, cy + 380], fill=black)
        draw.ellipse([cx - 65, cy - 40, cx + 65, cy + 80], fill=black)
        # Крылья бабочки
        draw.polygon([(cx - 50, cy - 30), (cx - 150, cy - 110), (cx - 120, cy + 20), (cx - 40, cy)], fill=black)
        draw.polygon([(cx + 50, cy - 30), (cx + 150, cy - 110), (cx + 120, cy + 20), (cx + 40, cy)], fill=black)
        # Глаза фасеточные
        draw.ellipse([cx - 45, cy + 5, cx - 15, cy + 35], fill=accent)
        draw.ellipse([cx + 15, cy + 5, cx + 45, cy + 35], fill=accent)

    elif idx == 15:
        # 15. Женщина-вамп в домино-маске
        draw.ellipse([cx - 140, cy + 100, cx + 140, cy + 380], fill=black)
        draw.ellipse([cx - 75, cy - 45, cx + 75, cy + 85], fill=black)
        # Маска домино
        draw.polygon([(cx - 70, cy), (cx - 30, cy - 20), (cx, cy), (cx + 30, cy - 20), (cx + 70, cy),
                      (cx + 40, cy + 25), (cx, cy + 15), (cx - 40, cy + 25)], fill=accent)
        # Прорези для глаз
        draw.ellipse([cx - 50, cy - 2, cx - 20, cy + 18], fill=black)
        draw.ellipse([cx + 20, cy - 2, cx + 50, cy + 18], fill=black)

    elif idx == 16:
        # 16. Неоновый зайчик Playboy-демон
        draw.ellipse([cx - 130, cy + 100, cx + 130, cy + 380], fill=black)
        draw.ellipse([cx - 70, cy - 40, cx + 70, cy + 85], fill=black)
        # Одно ухо прямое, второе согнутое
        draw.polygon([(cx - 50, cy - 30), (cx - 65, cy - 180), (cx - 20, cy - 170), (cx - 15, cy - 40)], fill=black)
        draw.polygon([(cx + 15, cy - 40), (cx + 30, cy - 130), (cx + 80, cy - 90), (cx + 45, cy - 30)], fill=black)
        # Глаза сердечки
        draw.ellipse([cx - 45, cy + 10, cx - 20, cy + 35], fill=accent)
        draw.ellipse([cx + 20, cy + 10, cx + 45, cy + 35], fill=accent)

    elif idx == 17:
        # 17. Самурайка с катаной за спиной
        draw.ellipse([cx - 140, cy + 100, cx + 140, cy + 380], fill=black)
        draw.ellipse([cx - 75, cy - 40, cx + 75, cy + 85], fill=black)
        # Катана наискосок
        draw.line([cx - 130, cy + 150, cx + 130, cy - 130], fill=accent, width=8)
        # Прическа пучок
        draw.ellipse([cx - 30, cy - 100, cx + 30, cy - 40], fill=black)
        # Глаза узкие
        draw.line([cx - 50, cy + 15, cx - 15, cy + 15], fill=accent, width=6)
        draw.line([cx + 15, cy + 15, cx + 50, cy + 15], fill=accent, width=6)

    elif idx == 18:
        # 18. Пылающая фурия (языки пламени из головы)
        draw.ellipse([cx - 140, cy + 100, cx + 140, cy + 380], fill=black)
        draw.ellipse([cx - 75, cy - 35, cx + 75, cy + 85], fill=black)
        # Языки пламени
        for fx, fy in [(-60, -110), (-30, -150), (0, -170), (30, -150), (60, -110)]:
            draw.polygon([(fx - 15, cy - 30), (fx, fy), (fx + 15, cy - 30)], fill=black)
        # Глаза
        draw.ellipse([cx - 45, cy + 10, cx - 15, cy + 35], fill=accent)
        draw.ellipse([cx + 15, cy + 10, cx + 45, cy + 35], fill=accent)

    elif idx == 19:
        # 19. Неоновая кукла с нимбом и рожками одновременно
        draw.ellipse([cx - 140, cy + 100, cx + 140, cy + 380], fill=black)
        draw.ellipse([cx - 70, cy - 40, cx + 70, cy + 85], fill=black)
        # Нимб над головой
        draw.ellipse([cx - 60, cy - 120, cx + 60, cy - 80], outline=accent, width=6)
        # Рожки под нимбом
        draw.polygon([(cx - 50, cy - 30), (cx - 75, cy - 80), (cx - 30, cy - 45)], fill=black)
        draw.polygon([(cx + 50, cy - 30), (cx + 75, cy - 80), (cx + 30, cy - 45)], fill=black)
        # Глаза
        draw.ellipse([cx - 45, cy + 15, cx - 15, cy + 35], fill=accent)
        draw.ellipse([cx + 15, cy + 15, cx + 45, cy + 35], fill=accent)

    else:
        # 20. Роковое яблоко греха с червячком-рожком
        draw.ellipse([cx - 140, cy + 110, cx + 140, cy + 380], fill=black)
        # Голова-яблоко с выемкой
        draw.ellipse([cx - 80, cy - 50, cx - 5, cy + 30], fill=black)
        draw.ellipse([cx + 5, cy - 50, cx + 80, cy + 30], fill=black)
        draw.polygon([(cx - 75, cy), (cx, cy + 85), (cx + 75, cy)], fill=black)
        # Черенок с листком
        draw.line([cx, cy - 45, cx - 10, cy - 110], fill=accent, width=8)
        draw.ellipse([cx - 35, cy - 125, cx, cy - 95], fill=accent)
        # Искушающие глаза
        draw.ellipse([cx - 45, cy + 15, cx - 15, cy + 40], fill=accent)
        draw.ellipse([cx + 15, cy + 15, cx + 45, cy + 40], fill=accent)

    # Рамка вокруг
    draw.rounded_rectangle([15, 15, 585, 585], radius=24, outline=black, width=8)

def main():
    print("🎨 Generating 20 completely unique Male and 20 Female Pure-Style Avatars...")
    width, height = 600, 600
    cx, cy = width // 2, height // 2

    for i in range(1, 21):
        # 1. Мужской аватар
        pal_m = PSYCHEDELIC_PALETTES[i - 1]
        img_m = render_wavy_background(width, height, pal_m[0], pal_m[1], wave_type=i)
        draw_m = ImageDraw.Draw(img_m)
        draw_male_creature(draw_m, cx, cy, i, pal_m[0])
        out_m = os.path.join(MALE_DIR, f"male_{i:02d}.jpg")
        img_m.save(out_m, "JPEG", quality=95)

        # 2. Женский аватар
        pal_f = PSYCHEDELIC_PALETTES[(i + 7) % len(PSYCHEDELIC_PALETTES)]
        img_f = render_wavy_background(width, height, pal_f[0], pal_f[1], wave_type=i + 1)
        draw_f = ImageDraw.Draw(img_f)
        draw_female_creature(draw_f, cx, cy, i, pal_f[1])
        out_f = os.path.join(FEMALE_DIR, f"female_{i:02d}.jpg")
        img_f.save(out_f, "JPEG", quality=95)

    print("✅ Successfully generated 20 distinct Male and 20 distinct Female Pure-Style Avatars!")

if __name__ == "__main__":
    main()
