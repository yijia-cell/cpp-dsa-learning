# -*- coding: utf-8 -*-
"""
==========================================================
  智"绘"祖国 · 代码传情
  青春告白祖国 · 西电95周年 · 长征 · 电波 · 中国红 · 传承三系精神
==========================================================
  运行环境: Python 3.8+   (需安装 pygame 或 pygame-ce)
  安装依赖: pip install pygame-ce -i https://pypi.tuna.tsinghua.edu.cn/simple
  运行程序: python xidian_95.py
  操作说明: 空格 = 暂停/继续     S = 截图     ESC / Q = 退出
  建议录制: 全屏运行, 录屏软件录制 24 秒(一整轮动画)导出 GIF
==========================================================
"""

import os
import sys
import math
import random

try:
    import pygame
except ImportError:
    print("请先安装 pygame 或 pygame-ce:")
    print("pip install pygame-ce -i https://pypi.tuna.tsinghua.edu.cn/simple")
    sys.exit(1)

# ============================ 基础参数 ============================
W, H = 1280, 720          # 画布尺寸
FPS = 60                  # 帧率
LOOP = 24.0               # 一轮动画总时长(秒), 循环播放

# ---------------------------- 配色(中国红体系) ----------------------------
CHINA_RED = (222, 41, 16)      # 中国红
GOLD = (255, 205, 90)          # 描金
LIGHT_GOLD = (255, 238, 190)   # 亮金
WARM_WHITE = (255, 244, 236)   # 暖白
PINKISH = (255, 200, 170)      # 淡粉金
SHADOW = (40, 5, 5)            # 文字阴影色，取代发光

# ============================ 中文字体加载 ============================
FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyhbd.ttc",      # 微软雅黑 粗体
    "C:/Windows/Fonts/msyh.ttc",        # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",      # 黑体
    "C:/Windows/Fonts/simsun.ttc",      # 宋体
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
]

_FONT_PATH = None

def _find_font_path():
    global _FONT_PATH
    if _FONT_PATH is None:
        for p in FONT_CANDIDATES:
            if os.path.exists(p):
                _FONT_PATH = p
                break
        else:
            _FONT_PATH = ""
    return _FONT_PATH

_fonts = {}

def F(size, bold=False):
    key = (size, bold)
    if key in _fonts:
        return _fonts[key]
    path = _find_font_path()
    if path:
        f = pygame.font.Font(path, size)
        f.set_bold(bold)
    else:
        f = pygame.font.SysFont("microsoftyahei,simhei,arial", size, bold=bold)
    _fonts[key] = f
    return f

# ============================ 文字渲染(极简清晰版) ============================
_tex_cache = {}

def text_surface(text, size, color, shadow_color=SHADOW, bold=True, pad=6):
    """渲染清晰文字，只带简单阴影，无任何发光和重影"""
    key = (text, size, tuple(color), tuple(shadow_color) if shadow_color else None, bold, pad)
    if key in _tex_cache:
        return _tex_cache[key]

    font = F(size, bold)
    base = font.render(text, True, color)
    w, h = base.get_size()
    surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)

    if shadow_color:
        shadow = font.render(text, True, shadow_color)
        shadow.set_alpha(150)  # 阴影半透明，增加层次感但不干扰主文字
        surf.blit(shadow, (pad + 2, pad + 2))

    # 主文字直接贴在最上层
    surf.blit(base, (pad, pad))
    _tex_cache[key] = surf
    return surf

def blit_c(dst, surf, center, alpha=255):
    """居中贴图，只改变透明度，绝对不进行任何缩放避免模糊"""
    if alpha <= 0:
        return
    s = surf
    s.set_alpha(int(max(0, min(255, alpha))))
    dst.blit(s, s.get_rect(center=(int(center[0]), int(center[1]))))

# ============================ 工具函数 ============================
def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3

def scene_alpha(t, start, end, f=0.7):
    if t < start - f or t > end + f:
        return 0.0
    if t < start:
        return (t - (start - f)) / f
    if t > end:
        return max(0.0, 1 - (t - end) / f)
    return 1.0

def star_points(cx, cy, R, rot=-math.pi / 2):
    pts = []
    for i in range(10):
        r = R if i % 2 == 0 else R * 0.382
        a = rot + i * math.pi / 5
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def draw_star(layer, cx, cy, R, color, alpha):
    if alpha <= 0 or R <= 0:
        return
    pts = star_points(cx, cy, R)
    pygame.draw.polygon(layer, (*color, int(alpha)), pts)

def glow_circle(layer, center, radius, color, alpha, power=2.0, steps=34):
    if alpha <= 0:
        return
    for i in range(steps, 0, -1):
        k = i / steps
        a = int(alpha * (1 - k) ** power)
        if a <= 0:
            continue
        pygame.draw.circle(layer, (*color, a), center, int(radius * k))

def draw_waves(layer, center, tt, max_r=460, count=6, speed=0.45, color=(255, 80, 60), alpha=180):
    for i in range(count):
        ph = (tt * speed + i / count) % 1.0
        r = ph * max_r
        if r < 3:
            continue
        a = int(alpha * (1 - ph) ** 1.8)
        if a <= 0:
            continue
        w = max(1, int(3 * (1 - ph)) + 1)
        pygame.draw.circle(layer, (*color, a), center, int(r), w)

# 径向光晕贴图
_radial_cache = {}
def make_radial(radius, color, power=2.0, steps=64):
    size = radius * 2
    surf = pygame.Surface((size, size))
    surf.fill((0, 0, 0))
    step = max(1, radius // steps)
    for i in range(steps, 0, -1):
        d = i / steps
        a = (1 - d) ** power
        c = (int(color[0] * a), int(color[1] * a), int(color[2] * a))
        pygame.draw.circle(surf, c, (radius, radius), int(radius * d), step)
    return surf

def radial(radius, color, power=2.0):
    key = (radius, tuple(color), power)
    if key not in _radial_cache:
        _radial_cache[key] = make_radial(radius, color, power)
    return _radial_cache[key]

# ============================ 背景 ============================
_bg = None
def background():
    global _bg
    if _bg is not None:
        return _bg
    _bg = pygame.Surface((W, H))
    for y in range(H):
        k = y / H
        c = (int(12 + 44 * k), int(2 + 9 * k), int(5 + 13 * k))
        pygame.draw.line(_bg, c, (0, y), (W, y))
    g1 = radial(520, (110, 22, 16))
    _bg.blit(g1, g1.get_rect(center=(W // 2, H // 2 - 40)), special_flags=pygame.BLEND_RGB_ADD)
    g2 = radial(680, (70, 12, 12))
    _bg.blit(g2, g2.get_rect(center=(W // 2, H + 260)), special_flags=pygame.BLEND_RGB_ADD)
    return _bg

# ============================ 粒子: 星火 ============================
class Spark:
    __slots__ = ("x", "y", "vx", "vy", "r", "hue", "life", "maxlife")
    def __init__(self, anywhere=True):
        self.reset(anywhere)
    def reset(self, anywhere=True):
        self.x = random.uniform(0, W)
        self.y = random.uniform(0, H) if anywhere else H + random.uniform(10, 140)
        self.vx = random.uniform(-12, 12)
        self.vy = random.uniform(-48, -14)
        self.r = random.uniform(0.9, 2.7)
        self.hue = random.random()
        self.maxlife = random.uniform(2.5, 6.0)
        self.life = self.maxlife * (random.random() if anywhere else 1.0)
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        if self.life <= 0 or self.y < -30 or self.x < -30 or self.x > W + 30:
            self.reset(False)
    def draw(self, layer):
        k = max(0.0, min(1.0, self.life / self.maxlife)) ** 0.6
        a = int(230 * k)
        if a <= 3: return
        if self.hue < 0.6:
            c = (255, int(180 + 60 * self.hue), int(90 * self.hue))
        else:
            c = (255, int(70 + 50 * (1 - self.hue)), int(50 * (1 - self.hue)))
        pygame.draw.circle(layer, (*c, a), (int(self.x), int(self.y)), max(1, int(self.r)))

# ============================ 长征红飘带 ============================
def ribbon_point(k, tt):
    x = 90 + k * (W - 180)
    y = H * 0.68 - 120 * math.sin(k * math.pi * 1.45) + 30 * math.sin(k * math.pi * 3.0 + tt * 1.8)
    return x, y

def draw_ribbon(layer, tt, progress, alpha):
    if progress <= 0 or alpha <= 0: return
    n = 170
    cnt = max(2, int(n * progress))
    pts = [ribbon_point(i / n, tt) for i in range(cnt)]
    for i, (x, y) in enumerate(pts):
        k = i / max(1, cnt - 1)
        R = int(8 + 4 * math.sin(k * math.pi))
        pygame.draw.circle(layer, (188, 24, 30, alpha), (int(x), int(y)), R)
    for i in range(0, cnt, 2):
        x, y = pts[i]
        pygame.draw.circle(layer, (255, 118, 96, alpha // 3), (int(x), int(y) - 2), 3)

# ============================ 图形层绘制 ============================
def draw_graphics(layer, t, sparks):
    for s in sparks: s.draw(layer)
    draw_waves(layer, (W // 2, H // 2), t, max_r=640, count=4, speed=0.16, color=(255, 70, 50), alpha=38)

    # 场景一
    a1 = scene_alpha(t, 0.0, 4.6)
    if a1 > 0:
        cx, cy = W // 2, H // 2 - 30
        glow_circle(layer, (cx, cy), 430, (200, 45, 30), int(115 * a1), power=2.4)
        for i in range(3):
            ang = t * 0.6 + i * math.tau / 3
            draw_star(layer, cx + 330 * math.cos(ang), cy + 165 * math.sin(ang), 13, GOLD, 210 * a1)
    # 场景二
    a2 = scene_alpha(t, 4.4, 9.4)
    if a2 > 0:
        cx, cy = W // 2, 300
        tt = t - 4.4
        draw_waves(layer, (cx, cy), tt, max_r=470, count=6, speed=0.45, color=(255, 90, 65), alpha=int(190 * a2))
        glow_circle(layer, (cx, cy), 330, (220, 60, 40), int(95 * a2), power=2.0)
    # 场景三
    a3 = scene_alpha(t, 9.2, 14.4)
    if a3 > 0:
        tt = t - 9.2
        prog = min(1.0, tt / 2.0)
        draw_ribbon(layer, tt, prog, int(215 * a3))
        if prog > 0:
            x, y = ribbon_point(prog, tt)
            R = 16 + 4 * math.sin(t * 4)
            glow_circle(layer, (int(x), int(y)), 62, (255, 160, 60), int(130 * a3))
            draw_star(layer, x, y, R, GOLD, 255 * a3)
    # 场景四
    a4 = scene_alpha(t, 14.2, 19.4)
    if a4 > 0:
        cx, cy = W // 2, H // 2 - 20
        tt = t - 14.2
        draw_waves(layer, (cx, cy - 10), tt * 0.8, max_r=380, count=5, speed=0.4, color=(255, 120, 80), alpha=int(150 * a4))
        glow_circle(layer, (cx, cy - 10), 320, (200, 60, 40), int(75 * a4))
        ring_a = int(205 * a4)
        pygame.draw.circle(layer, (255, 210, 130, ring_a), (cx, cy - 10), 160, 3)
        pygame.draw.circle(layer, (255, 160, 100, ring_a // 2), (cx, cy - 10), 176, 1)
    # 场景五
    a5 = scene_alpha(t, 19.2, 23.6, 1.0)
    if a5 > 0:
        cx, cy = W // 2, H // 2 - 40
        glow_circle(layer, (cx, cy), 540, (210, 50, 30), int(140 * a5), power=2.6)
        draw_waves(layer, (cx, cy), t * 0.9, max_r=580, count=5, speed=0.5, color=(255, 90, 60), alpha=int(125 * a5))
        for i in range(6):
            ang = -t * 0.8 + i * math.tau / 6
            draw_star(layer, cx + 400 * math.cos(ang), cy + 205 * math.sin(ang), 14 + 3 * math.sin(t * 3 + i), GOLD, 220 * a5)

# ============================ 印章 ============================
def draw_seal(screen, center, alpha):
    if alpha <= 0: return
    size = 112
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(s, (198, 28, 28, 225), (0, 0, size, size), border_radius=10)
    pygame.draw.rect(s, (255, 232, 222, 240), (8, 8, size - 16, size - 16), 3, border_radius=6)
    f = F(30, True)
    for i, ch in enumerate("中国红"):
        img = f.render(ch, True, (255, 242, 238))
        s.blit(img, img.get_rect(center=(size // 2, 28 + i * 28)))
    s.set_alpha(int(255 * alpha))
    screen.blit(s, s.get_rect(center=center))

# ============================ 文字层绘制 ============================
def draw_texts(screen, t):
    # 场景一：青春告白祖国
    a1 = scene_alpha(t, 0.0, 4.6)
    if a1 > 0:
        cx, cy = W // 2, H // 2 - 30
        sa = scene_alpha(t, 0.7, 4.4, 0.7)
        if sa > 0:
            blit_c(screen, text_surface("青春告白祖国", 100, LIGHT_GOLD, GOLD), (cx, cy), 255 * sa)
        sb = scene_alpha(t, 1.7, 4.4, 0.7)
        if sb > 0:
            blit_c(screen, text_surface("以青春之名 · 向祖国告白", 36, PINKISH), (cx, cy + 112), 235 * sb)
        sc = scene_alpha(t, 2.5, 4.4, 0.7)
        if sc > 0:
            blit_c(screen, text_surface("西安电子科技大学 · 智绘祖国 代码传情", 26, (242, 165, 145)), (cx, cy + 172), 205 * sc)

    # 场景二：95
    a2 = scene_alpha(t, 4.4, 9.4)
    if a2 > 0:
        cx, cy = W // 2, 300
        sa = scene_alpha(t, 4.9, 9.2, 0.6)
        if sa > 0:
            blit_c(screen, text_surface("95", 300, GOLD, (255, 120, 60)), (cx, cy), 255 * sa)
        sc = scene_alpha(t, 5.6, 9.2, 0.6)
        if sc > 0:
            blit_c(screen, text_surface("电波不息 · 薪火相传", 34, PINKISH), (cx, 92), 215 * sc)
        sb = scene_alpha(t, 6.2, 9.2, 0.6)
        if sb > 0:
            blit_c(screen, text_surface("1931 — 2026", 42, LIGHT_GOLD, (255, 100, 60)), (cx, 520), 240 * sb)
            blit_c(screen, text_surface("西安电子科技大学建校 95 周年", 34, PINKISH), (cx, 582), 225 * sb)

    # 场景三：长征
    a3 = scene_alpha(t, 9.2, 14.4)
    if a3 > 0:
        sa = scene_alpha(t, 9.8, 14.2, 0.6)
        if sa > 0:
            blit_c(screen, text_surface("长  征", 84, LIGHT_GOLD, (255, 90, 60)), (W // 2, 138), 255 * sa)
            blit_c(screen, text_surface("半部电台起家 · 长征路上办学", 34, PINKISH), (W // 2, 218), 225 * sa)
        sb = scene_alpha(t, 11.2, 14.2, 0.6)
        if sb > 0:
            blit_c(screen, text_surface("电波所至 · 皆是信仰", 28, (255, 185, 160)), (W // 2, 268), 195 * sb)

    # 场景四：西电 · 三系精神
    a4 = scene_alpha(t, 14.2, 19.4)
    if a4 > 0:
        cx, cy = W // 2, H // 2 - 20
        sa = scene_alpha(t, 14.8, 19.2, 0.6)
        if sa > 0:
            blit_c(screen, text_surface("西电", 110, LIGHT_GOLD, (255, 90, 60)), (cx, cy - 30), 255 * sa)
            blit_c(screen, text_surface("传承三系精神", 52, GOLD, (255, 90, 50)), (cx, cy + 138), 255 * sa)
        sb = scene_alpha(t, 15.9, 19.2, 0.6)
        if sb > 0:
            blit_c(screen, text_surface("艰苦奋斗 · 自强不息 · 求真务实 · 爱国为民", 30, PINKISH), (cx, cy + 212), 225 * sb)

    # 场景五：大团圆
    a5 = scene_alpha(t, 19.2, 23.6, 1.0)
    if a5 > 0:
        cx, cy = W // 2, H // 2 - 40
        sa = scene_alpha(t, 19.8, 23.4, 0.8)
        if sa > 0:
            blit_c(screen, text_surface("青春告白祖国", 110, LIGHT_GOLD, (255, 120, 60)), (cx, cy - 25), 255 * sa)
        sb = scene_alpha(t, 20.9, 23.4, 0.8)
        if sb > 0:
            blit_c(screen, text_surface("中国红 · 电波情 · 三系魂", 36, PINKISH), (cx, cy + 92), 225 * sb)
        sc = scene_alpha(t, 21.7, 23.4, 0.8)
        if sc > 0:
            blit_c(screen, text_surface("西安电子科技大学 · 智绘祖国 代码传情", 26, (255, 180, 155)), (cx, cy + 158), 205 * sc)
            draw_seal(screen, (W - 190, H - 150), sc)

# ============================ 合成一帧 ============================
_fx = None
def fx_layer():
    global _fx
    if _fx is None:
        _fx = pygame.Surface((W, H), pygame.SRCALPHA)
    return _fx

def render(screen, t, sparks):
    screen.blit(background(), (0, 0))
    layer = fx_layer()
    layer.fill((0, 0, 0, 0))
    draw_graphics(layer, t, sparks)
    screen.blit(layer, (0, 0))
    draw_texts(screen, t)

    fade = 0.0
    if t < 0.7: fade = 1 - t / 0.7
    elif t > LOOP - 0.7: fade = (t - (LOOP - 0.7)) / 0.7
    if fade > 0:
        black = pygame.Surface((W, H))
        black.set_alpha(int(255 * min(1.0, fade)))
        screen.blit(black, (0, 0))

# ============================ 主循环 ============================
def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("智绘祖国 · 代码传情 | 青春告白祖国 · 西电95周年")
    clock = pygame.time.Clock()
    sparks = [Spark() for _ in range(170)]

    t = 0.0
    paused = False
    shot_id = 0
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif e.key == pygame.K_SPACE:
                    paused = not paused
                elif e.key == pygame.K_s:
                    shot_id += 1
                    name = "xidian_95_shot_%02d.png" % shot_id
                    pygame.image.save(screen, name)
                    print("已保存截图:", name)

        if not paused:
            t += dt
            if t >= LOOP: t -= LOOP
            for s in sparks: s.update(dt)

        render(screen, t, sparks)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
