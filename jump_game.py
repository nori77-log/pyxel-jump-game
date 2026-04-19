# ================================================
#  PYXEL JUMP GAME
#  横スクロールジャンピングゲーム
#  VSCode拡張機能「Pyxel」で実行：
#    コマンドパレット → "Pyxel: Run Script"
# ================================================

import pyxel
import random

# ---- 定数 ----------------------------------------
WIDTH  = 200
HEIGHT = 150
FPS    = 30

GRAVITY     = 0.5
JUMP_POWER  = -8
PLAYER_SPD  = 2
SCROLL_SPD  = 2

# Pyxel 16色パレット番号
COL_BG_SKY   = 1   # 暗い青
COL_BG_CLOUD = 7   # 白
COL_GROUND   = 11  # 緑
COL_PLAYER   = 8   # 赤
COL_COIN     = 10  # 黄
COL_SPIKE    = 2   # 赤紫
COL_TEXT     = 7   # 白
COL_SCORE    = 10  # 黄
COL_MOUNTAIN = 5   # 暗い青緑

# ---- ヘルパー関数 --------------------------------
def rrect(x, y, w, h, col):
    """塗りつぶし矩形"""
    pyxel.rect(x, y, w, h, col)

def draw_player(x, y, jumping):
    """プレイヤーをドット絵風に描画"""
    # 胴体
    rrect(x,   y,   8, 8, COL_PLAYER)
    # 目
    pyxel.pset(x+2, y+2, 7)
    pyxel.pset(x+5, y+2, 7)
    # 足（ジャンプ中は縮める）
    if not jumping:
        rrect(x+1, y+8, 2, 3, COL_PLAYER)
        rrect(x+5, y+8, 2, 3, COL_PLAYER)
    else:
        rrect(x+1, y+7, 2, 2, COL_PLAYER)
        rrect(x+5, y+7, 2, 2, COL_PLAYER)

# ---- ゲームクラス --------------------------------
class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="PYXEL JUMP GAME", fps=FPS)
        self.reset()
        pyxel.run(self.update, self.draw)

    def reset(self):
        # プレイヤー
        self.px = 30
        self.py = HEIGHT - 24
        self.vy = 0
        self.on_ground = True
        self.jump_count = 0   # ジャンプ回数（最大2）
        self.dead = False

        # ゲーム状態
        self.coins_score = 0   # コイン取得スコア
        self.dist        = 0   # 距離スコア
        self.scroll = 0
        self.frame  = 0
        self.started = False
        self.hi_coins = getattr(self, "hi_coins", 0)
        self.hi_dist  = getattr(self, "hi_dist",  0)

        # 地面タイル（x座標のみ管理）
        self.ground_y = HEIGHT - 16   # 地面Y

        # 障害物・コイン
        self.spikes = []   # (x, y, w)
        self.coins  = []   # (x, y, alive)
        self.clouds = [(random.randint(0, WIDTH), random.randint(20, 60)) for _ in range(5)]

        # 初回ステージ生成
        for i in range(6):
            self._spawn_objects(WIDTH + i * 60)

    def _spawn_objects(self, base_x):
        """ランダムにスパイクとコインを生成"""
        x = base_x + random.randint(0, 30)
        # スパイク
        if random.random() < 0.55:
            self.spikes.append([x, self.ground_y - 6, 8])
        # コイン（スパイクと別の位置）
        cx = x + random.randint(20, 50)
        cy = self.ground_y - random.randint(24, 48)
        self.coins.append([cx, cy, True])

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        # タイトル画面でスペース/上で開始
        if not self.started:
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_UP):
                self.started = True
            return

        # ゲームオーバー後リセット
        if self.dead:
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_UP):
                self.hi_coins = max(self.hi_coins, self.coins_score)
                self.hi_dist  = max(self.hi_dist,  self.dist)
                self.reset()
                self.started = True
            return

        self.frame += 1
        self.scroll += SCROLL_SPD

        # --- プレイヤー入力（2段ジャンプ対応）---
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_UP):
            if self.jump_count < 2:
                self.vy = JUMP_POWER
                self.on_ground = False
                self.jump_count += 1

        # --- 重力 ---
        self.vy += GRAVITY
        self.py += self.vy

        # --- 地面着地 ---
        if self.py >= self.ground_y - 8:
            self.py = self.ground_y - 8
            self.vy = 0
            self.on_ground = True
            self.jump_count = 0

        # --- スクロールに合わせてオブジェクト移動 ---
        for s in self.spikes:
            s[0] -= SCROLL_SPD
        for c in self.coins:
            c[0] -= SCROLL_SPD
        for i, (cx, cy) in enumerate(self.clouds):
            self.clouds[i] = (cx - 0.4, cy)
            if cx < -20:
                self.clouds[i] = (WIDTH + random.randint(0, 40), random.randint(20, 60))

        # --- 画面外オブジェクト除去 ---
        self.spikes = [s for s in self.spikes if s[0] > -16]
        self.coins  = [c for c in self.coins  if c[0] > -16]

        # --- 新オブジェクト補充 ---
        if self.frame % 55 == 0:
            self._spawn_objects(WIDTH + 40)

        # --- コイン取得判定 ---
        px, py = int(self.px), int(self.py)
        for c in self.coins:
            if c[2]:
                if self._rects_overlap(px, py, 8, 8, int(c[0]), int(c[1]), 6, 6):
                    c[2] = False
                    self.coins_score += 10

        # --- スパイク衝突判定 ---
        for s in self.spikes:
            if self._rects_overlap(px, py, 8, 8, int(s[0])+1, int(s[1])+2, s[2]-2, 4):
                self.dead = True

        # --- 距離カウント ---
        self.dist += 1



    def _rects_overlap(self, ax, ay, aw, ah, bx, by, bw, bh):
        return (ax < bx + bw and ax + aw > bx and
                ay < by + bh and ay + ah > by)

    # ---- 描画 -------------------------------------
    def draw(self):
        pyxel.cls(COL_BG_SKY)

        # 山シルエット（背景）
        self._draw_mountains()

        # 雲
        for cx, cy in self.clouds:
            rrect(int(cx), int(cy), 18, 7, COL_BG_CLOUD)
            rrect(int(cx)+4, int(cy)-4, 10, 6, COL_BG_CLOUD)

        # 地面
        rrect(0, self.ground_y, WIDTH, HEIGHT - self.ground_y, COL_GROUND)
        rrect(0, self.ground_y, WIDTH, 2, 11)

        # スパイク（三角形風）
        for s in self.spikes:
            x, y, w = int(s[0]), int(s[1]), s[2]
            pyxel.tri(x, y+6, x+w//2, y, x+w, y+6, COL_SPIKE)

        # コイン
        for c in self.coins:
            if c[2]:
                cx, cy = int(c[0]), int(c[1])
                pyxel.circ(cx+3, cy+3, 3, COL_COIN)
                pyxel.circ(cx+3, cy+3, 2, 9)

        # プレイヤー
        draw_player(int(self.px), int(self.py), not self.on_ground)

        # UI
        pyxel.text(4, 4,  f"COIN:{self.coins_score:04d}", COL_SCORE)
        pyxel.text(4, 12, f"DIST:{self.dist:06d}",        COL_TEXT)
        pyxel.text(4, 20, f"BEST COIN:{self.hi_coins:04d}", COL_SCORE)
        pyxel.text(4, 28, f"BEST DIST:{self.hi_dist:06d}", COL_TEXT)
        pyxel.text(WIDTH - 52, 4, "SPACE:JUMP", COL_TEXT)

        # タイトル
        if not self.started:
            self._draw_overlay()
            pyxel.text(WIDTH//2-38, HEIGHT//2-8, "PYXEL JUMP GAME", 10)
            pyxel.text(WIDTH//2-38, HEIGHT//2+4, "SPACE or UP: START", 7)

        # ゲームオーバー
        if self.dead:
            self._draw_overlay()
            pyxel.text(WIDTH//2-26, HEIGHT//2-8, "GAME OVER", 8)
            pyxel.text(WIDTH//2-40, HEIGHT//2+4, "SPACE or UP: RETRY", 7)

    def _draw_mountains(self):
        """背景の山を描画"""
        pts = [0, 80, 30, 50, 60, 70, 90, 40, 120, 65, 150, 45, 180, 60, 200, 80]
        for i in range(0, len(pts)-2, 2):
            x1, y1, x2, y2 = pts[i], pts[i+1], pts[i+2], pts[i+3]
            # 簡易三角で山
            mid_y = min(y1, y2) - 15
            mid_x = (x1 + x2) // 2
            pyxel.tri(x1, y1, mid_x, mid_y, x2, y2, COL_MOUNTAIN)

    def _draw_overlay(self):
        for y in range(HEIGHT//2 - 16, HEIGHT//2 + 18):
            pyxel.line(0, y, WIDTH, y, 0)

App()
