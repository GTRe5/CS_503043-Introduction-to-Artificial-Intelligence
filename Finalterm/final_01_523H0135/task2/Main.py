"""
Main.py - Pygame UI for 9x9 Tic-Tac-Toe.

The UI layer only communicates with Solution.  No game logic lives here.
"""

import sys
import math
import random
import pygame

from Solution import Solution

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
WIDTH, HEIGHT  = 600, 700
ROWS, COLS     = 9, 9
SQ             = WIDTH // COLS          # square size = 66 px

# colours
BG_COLOR       = (255, 255, 255)
LINE_COLOR     = (200, 200, 200)
PIECE_COLOR    = (50,  50,  50)
TEXT_COLOR     = (0,   0,   0)
HIGHLIGHT_CLR  = (255, 0,   0)
BTN_WHITE      = (255, 255, 255)

BLUE           = (70,  130, 180)
BLUE_H         = (100, 160, 210)
AMBER          = (180, 130, 70)
AMBER_H        = (210, 160, 100)
RED_BTN        = (180, 70,  70)
RED_BTN_H      = (210, 100, 100)
PURPLE         = (100, 100, 180)
PURPLE_H       = (130, 130, 210)
GRAY           = (180, 180, 180)

LINE_W         = 3
RADIUS         = SQ // 3
SPACE          = SQ // 4

SAVE_DIR       = "Storage"

# ─────────────────────────────────────────────────────────────────────────────
# PYGAME INIT
# ─────────────────────────────────────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tic Tac Toe Simulator")
font       = pygame.font.SysFont(None, 40)
small_font = pygame.font.SysFont(None, 24)
clock      = pygame.time.Clock()

pen_image = pygame.image.load("Png/pen.png").convert_alpha()
pen_image = pygame.transform.scale(pen_image, (90, 90))


# ─────────────────────────────────────────────────────────────────────────────
# BUTTON RECTS
# ─────────────────────────────────────────────────────────────────────────────
RESET_RECT = pygame.Rect(WIDTH - 120, HEIGHT - 48, 100, 42)
UNDO_RECT  = pygame.Rect(WIDTH - 240, HEIGHT - 48, 100, 42)
REDO_RECT = pygame.Rect(WIDTH - 480, HEIGHT - 48, 100, 42)
HOME_RECT  = pygame.Rect(WIDTH - 360, HEIGHT - 48, 100, 42)

INTRO_NEW_RECT  = pygame.Rect(WIDTH//2 - 110, HEIGHT//2 - 60,  220, 50)
INTRO_CONT_RECT = pygame.Rect(WIDTH//2 - 110, HEIGHT//2,       220, 50)
INTRO_TUT_RECT  = pygame.Rect(WIDTH//2 - 110, HEIGHT//2 + 60,  220, 50)
INTRO_EXIT_RECT = pygame.Rect(WIDTH//2 - 110, HEIGHT//2 + 120, 220, 50)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def load_bg():
    img = pygame.image.load("Png/background.png").convert()
    return pygame.transform.scale(img, (WIDTH, HEIGHT))


def draw_btn(rect, label, mouse, color, hover, enabled=True):
    c = (color if enabled else GRAY)
    if enabled and rect.collidepoint(mouse):
        c = hover
    pygame.draw.rect(screen, c, rect, border_radius=5)
    surf = font.render(label, True, BTN_WHITE)
    screen.blit(surf, surf.get_rect(center=rect.center))


def draw_grid():
    for i in range(1, ROWS):
        pygame.draw.line(screen, LINE_COLOR,
                         (0, i * SQ), (WIDTH, i * SQ), LINE_W)
    for i in range(1, COLS):
        pygame.draw.line(screen, LINE_COLOR,
                         (i * SQ, 0), (i * SQ, HEIGHT - 100), LINE_W)


def draw_pieces(state, skip=None):
    skip = skip or set()
    for r in range(ROWS):
        for c in range(COLS):
            if (r, c) in skip:
                continue
            sym = state.grid[r][c]
            cx  = c * SQ + SQ // 2
            cy  = r * SQ + SQ // 2
            if sym == "O":
                for _ in range(6):
                    ox, oy = random.randint(-2, 2), random.randint(-2, 2)
                    pygame.draw.ellipse(screen, PIECE_COLOR,
                                        (cx - RADIUS + ox, cy - RADIUS + oy,
                                         RADIUS * 2, RADIUS * 2), 1)
            elif sym == "X":
                for _ in range(5):
                    ox, oy = random.randint(-2, 2), random.randint(-2, 2)
                    s1 = (c * SQ + SPACE + ox, r * SQ + SPACE + oy)
                    e1 = (c * SQ + SQ - SPACE + ox, r * SQ + SQ - SPACE + oy)
                    s2 = (c * SQ + SPACE + ox, r * SQ + SQ - SPACE + oy)
                    e2 = (c * SQ + SQ - SPACE + ox, r * SQ + SPACE + oy)
                    pygame.draw.aaline(screen, PIECE_COLOR, s1, e1)
                    pygame.draw.aaline(screen, PIECE_COLOR, s2, e2)


def draw_status(text, sub=None):
    pygame.draw.rect(screen, BG_COLOR, (0, HEIGHT - 100, WIDTH, 100))
    screen.blit(font.render(text, True, TEXT_COLOR), (10, HEIGHT - 98))
    if sub:
        screen.blit(small_font.render(sub, True, TEXT_COLOR), (10, HEIGHT - 68))


def cell_center(r, c):
    return c * SQ + SQ // 2, r * SQ + SQ // 2


def animate_line(line, state):
    """Animated red line drawn over the winning cells."""
    sp = cell_center(*line[0])
    ep = cell_center(*line[-1])
    total = math.hypot(ep[0] - sp[0], ep[1] - sp[1])
    progress = 0
    bg = load_bg()
    while progress < total:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        screen.blit(bg, (0, 0))
        draw_pieces(state)
        draw_grid()
        progress = min(progress + 10, total)
        ratio = progress / total
        cx = sp[0] + (ep[0] - sp[0]) * ratio
        cy = sp[1] + (ep[1] - sp[1]) * ratio
        pygame.draw.line(screen, HIGHLIGHT_CLR, sp, (cx, cy), 6)
        pygame.display.flip()
        clock.tick(60)


def animate_draw(r, c, sym, state, winning_line):
    """Hand-drawing animation with a moving pen cursor."""
    cx, cy = cell_center(r, c)
    bg     = load_bg()

    for step in range(16):
        progress = step / 15
        screen.blit(bg, (0, 0))
        draw_grid()
        draw_pieces(state, skip={(r, c)})
        if winning_line:
            animate_line(winning_line, state)

        if sym == "O":
            angle = progress * 2 * math.pi
            rect  = (cx - RADIUS, cy - RADIUS, RADIUS * 2, RADIUS * 2)
            pygame.draw.arc(screen, PIECE_COLOR, rect, 0, angle, 2)
            px = cx + RADIUS * math.cos(angle) - 45
            py = cy + RADIUS * math.sin(angle) - 45
        else:                                    # X
            length = SQ - 2 * SPACE
            s1 = (c * SQ + SPACE, r * SQ + SPACE)
            off = int(progress * length)
            pygame.draw.aaline(screen, PIECE_COLOR, s1,
                               (s1[0] + off, s1[1] + off))
            if progress > 0.5:
                s2  = (c * SQ + SPACE, r * SQ + SQ - SPACE)
                off2 = int((progress - 0.5) * 2 * length)
                pygame.draw.aaline(screen, PIECE_COLOR, s2,
                                   (s2[0] + off2, s2[1] - off2))
                px, py = s2[0] + off2 - 45, s2[1] - off2 - 45
            else:
                px, py = s1[0] + off - 45, s1[1] + off - 45

        screen.blit(pen_image, (px, py))
        pygame.display.flip()
        clock.tick(30)


# ─────────────────────────────────────────────────────────────────────────────
# SCREENS
# ─────────────────────────────────────────────────────────────────────────────
def screen_difficulty() -> int:
    """Return the chosen depth limit (2 / 3 / 5)."""
    bg     = load_bg()
    easy   = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 70, 200, 50)
    medium = pygame.Rect(WIDTH//2 - 100, HEIGHT//2,      200, 50)
    hard   = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 70, 200, 50)

    while True:
        screen.blit(bg, (0, 0))
        mouse = pygame.mouse.get_pos()
        title = font.render("Select Difficulty", True, TEXT_COLOR)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
        draw_btn(easy,   "Easy",   mouse, BLUE,  BLUE_H)
        draw_btn(medium, "Medium", mouse, BLUE,  BLUE_H)
        draw_btn(hard,   "Hard",   mouse, BLUE,  BLUE_H)
        pygame.display.update()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if easy.collidepoint(ev.pos):   return 2
                if medium.collidepoint(ev.pos): return 3
                if hard.collidepoint(ev.pos):   return 5


def screen_tutorial():
    """
    Two-page interactive tutorial overlay.

    Page 0 - How to Play  : rules + animated mini-board showing 4-in-a-row
    Page 1 - Controls & Tips: mouse/button guide + difficulty breakdown
    """

    # ── local colour palette ──────────────────────────────────────────────────
    CARD      = (245, 245, 240)
    CARD_BDR  = (180, 180, 170)
    HDR_CLR   = (70,  130, 180)
    SEC_CLR   = (100, 100, 180)
    TXT_DARK  = (30,  30,  30)
    TXT_MID   = (90,  90,  90)
    WIN_RED   = (210, 60,  60)
    DOT_ON    = (70,  130, 180)
    DOT_OFF   = (200, 200, 200)
    GRN       = (70,  160, 80)
    GRN_H     = (100, 190, 110)

    # ── extra fonts ───────────────────────────────────────────────────────────
    title_f  = pygame.font.SysFont(None, 46)
    body_f   = pygame.font.SysFont(None, 26)
    label_f  = pygame.font.SysFont(None, 22)
    btn_f    = pygame.font.SysFont(None, 30)

    # ── card geometry ─────────────────────────────────────────────────────────
    CX, CY   = WIDTH // 2, HEIGHT // 2
    CW, CH   = 540, 490
    card     = pygame.Rect(CX - CW // 2, CY - CH // 2, CW, CH)

    # ── nav button rects ──────────────────────────────────────────────────────
    BW, BH = 110, 36
    next_r = pygame.Rect(card.right  - BW - 16, card.bottom - BH - 14, BW, BH)
    back_r = pygame.Rect(card.left   +      16, card.bottom - BH - 14, BW, BH)
    got_r  = pygame.Rect(CX - BW // 2,          card.bottom - BH - 14, BW, BH)

    # ── mini demo board (5x5) ─────────────────────────────────────────────────
    MS  = 36      # cell size
    MN  = 5       # 5x5
    MP  = 4       # padding between cells
    MBOARD = [
        [".", ".", ".", ".", "."],
        [".", "X", ".", "O", "."],
        [".", ".", "X", "O", "."],
        [".", "O", ".", "X", "."],
        [".", ".", ".", ".", "X"],
    ]
    WIN_CELLS = {(1, 1), (2, 2), (3, 3), (4, 4)}   # diagonal X win

    def mini_cc(r, c, ox, oy):
        return (ox + c * (MS + MP) + MP + MS // 2,
                oy + r * (MS + MP) + MP + MS // 2)

    def draw_mini_board(ox, oy, tick):
        total = MN * (MS + MP) + MP
        pygame.draw.rect(screen, (228, 228, 222),
                         (ox, oy, total, total), border_radius=8)
        # grid
        for i in range(MN + 1):
            gx = ox + i * (MS + MP) + MP - MP // 2
            gy = oy + i * (MS + MP) + MP - MP // 2
            pygame.draw.line(screen, (200,200,200),
                             (gx, oy + MP), (gx, oy + total - MP), 1)
            pygame.draw.line(screen, (200,200,200),
                             (ox + MP, gy), (ox + total - MP, gy), 1)
        # pieces
        for r in range(MN):
            for c in range(MN):
                cx2, cy2 = mini_cc(r, c, ox, oy)
                sym      = MBOARD[r][c]
                is_win   = (r, c) in WIN_CELLS
                if is_win:
                    pygame.draw.rect(screen, (255, 240, 220),
                                     (cx2 - MS//2 + 2, cy2 - MS//2 + 2,
                                      MS - 4, MS - 4), border_radius=4)
                if sym == "X":
                    clr = WIN_RED if is_win else (55, 55, 55)
                    sp  = MS // 4
                    pygame.draw.line(screen, clr,
                                     (cx2 - MS//2 + sp, cy2 - MS//2 + sp),
                                     (cx2 + MS//2 - sp, cy2 + MS//2 - sp), 2)
                    pygame.draw.line(screen, clr,
                                     (cx2 + MS//2 - sp, cy2 - MS//2 + sp),
                                     (cx2 - MS//2 + sp, cy2 + MS//2 - sp), 2)
                elif sym == "O":
                    pygame.draw.circle(screen, HDR_CLR,
                                       (cx2, cy2), MS // 2 - MS // 5, 2)

        # animated winning line
        p0 = mini_cc(1, 1, ox, oy)
        p1 = mini_cc(4, 4, ox, oy)
        dist  = math.hypot(p1[0]-p0[0], p1[1]-p0[1])
        prog  = min(1.0, (tick % 120) / 60)   # 0→1 over 60 frames, repeat
        ex    = p0[0] + (p1[0]-p0[0]) * prog
        ey    = p0[1] + (p1[1]-p0[1]) * prog
        pygame.draw.line(screen, WIN_RED, p0, (int(ex), int(ey)), 3)

        cap = label_f.render("4 in a row wins!", True, WIN_RED)
        screen.blit(cap, (ox + total//2 - cap.get_width()//2, oy + total + 6))

    # ── shared helpers ────────────────────────────────────────────────────────
    def pill_btn(rect, label, mouse, clr, hov, enabled=True):
        c = (GRAY if not enabled
             else hov if rect.collidepoint(mouse)
             else clr)
        pygame.draw.rect(screen, c, rect, border_radius=8)
        s = btn_f.render(label, True, BTN_WHITE if enabled else (160,160,160))
        screen.blit(s, s.get_rect(center=rect.center))

    def badge(x, y, text, clr):
        s = label_f.render(text, True, (255,255,255))
        w = s.get_width() + 18
        pygame.draw.rect(screen, clr, (x, y, w, 22), border_radius=5)
        screen.blit(s, (x + 9, y + 3))
        return w

    def row_icon_text(ix, iy, icon_str, text_str, icon_clr=HDR_CLR):
        ic = label_f.render(icon_str, True, icon_clr)
        screen.blit(ic, (ix, iy + 3))
        tx = body_f.render(text_str, True, TXT_DARK)
        screen.blit(tx, (ix + 40, iy + 4))

    def draw_dots(current, n=2):
        dy = card.bottom - 10
        for i in range(n):
            pygame.draw.circle(screen,
                               DOT_ON if i == current else DOT_OFF,
                               (CX + (i - n//2) * 18 + 5, dy), 5)

    # ── page 0: How to Play ───────────────────────────────────────────────────
    def draw_page_0(mouse, tick):
        lx  = card.x + 24
        ry  = card.y + 18

        # title
        t = title_f.render("How to Play", True, HDR_CLR)
        screen.blit(t, (lx, ry))
        pygame.draw.line(screen, HDR_CLR,
                         (lx, ry + 44), (lx + t.get_width(), ry + 44), 2)

        # mini board (right side)
        board_total = MN * (MS + MP) + MP
        bx = card.right - board_total - 20
        draw_mini_board(bx, card.y + 60, tick)

        ry = card.y + 66

        # RULES section
        badge(lx, ry, "RULES", SEC_CLR);  ry += 30
        rules = [
            ("You",  "You play as X,  AI plays as O"),
            ("1st",  "X always moves first"),
            ("Win",  "4 in a row: horiz, vert, diagonal"),
            ("AI",   "AI searches ahead before replying"),
        ]
        for icon, text in rules:
            ic = label_f.render(icon, True, (255,255,255))
            iw = ic.get_width() + 10
            pygame.draw.rect(screen, SEC_CLR, (lx, ry+2, iw+4, 20), border_radius=4)
            screen.blit(ic, (lx+4, ry+3))
            tx = body_f.render(text, True, TXT_DARK)
            screen.blit(tx, (lx + iw + 10, ry+3))
            ry += 33

        ry += 6
        badge(lx, ry, "BOARD", SEC_CLR);  ry += 30
        for line in [
            "9 x 9 grid  -  81 cells total",
            "Candidates are cells near existing pieces",
        ]:
            bt = body_f.render("•  " + line, True, TXT_MID)
            screen.blit(bt, (lx + 8, ry));  ry += 28

        pill_btn(next_r, "Next ->", mouse, BLUE, BLUE_H)

    # ── page 1: Controls & Tips ───────────────────────────────────────────────
    def draw_page_1(mouse, tick):
        lx = card.x + 24
        ry = card.y + 18

        t = title_f.render("Controls & Tips", True, HDR_CLR)
        screen.blit(t, (lx, ry))
        pygame.draw.line(screen, HDR_CLR,
                         (lx, ry + 44), (lx + t.get_width(), ry + 44), 2)
        ry = card.y + 66

        badge(lx, ry, "CONTROLS", SEC_CLR);  ry += 30
        controls = [
            ("[Click]", "Place your piece on an empty cell"),
            ("[Undo]",  "Reverts your last move + AI reply"),
            ("[Reset]", "Start a brand-new game immediately"),
            ("[Home]",  "Save & return to the main menu"),
            ("[ESC]",   "Close this overlay at any time"),
        ]
        for icon, text in controls:
            ic = label_f.render(icon, True, BTN_WHITE)
            iw = ic.get_width() + 8
            pygame.draw.rect(screen, HDR_CLR, (lx, ry+2, iw, 20), border_radius=4)
            screen.blit(ic, (lx+4, ry+3))
            tx = body_f.render(text, True, TXT_DARK)
            screen.blit(tx, (lx + iw + 10, ry+3))
            ry += 31

        ry += 8
        badge(lx, ry, "DIFFICULTY", (170, 95, 55));  ry += 30
        diffs = [
            ((80,  175, 80),  "Easy",   "Depth 2  -  relaxed, casual"),
            ((190, 150, 50),  "Medium", "Depth 3  -  balanced challenge"),
            ((190, 65,  65),  "Hard",   "Depth 5  -  strong, takes longer"),
        ]
        for clr, lbl, desc in diffs:
            pygame.draw.rect(screen, clr, (lx, ry+1, 62, 22), border_radius=5)
            ls = label_f.render(lbl, True, (255,255,255))
            screen.blit(ls, (lx + 31 - ls.get_width()//2, ry+4))
            ds = body_f.render(desc, True, TXT_MID)
            screen.blit(ds, (lx + 72, ry+4))
            ry += 30

        pill_btn(back_r, "<- Back", mouse, AMBER, AMBER_H)
        pill_btn(got_r,  "Got it!", mouse, GRN,   GRN_H)

    # ── main loop ─────────────────────────────────────────────────────────────
    bg   = load_bg()
    page = 0
    tick = 0

    while True:
        mouse = pygame.mouse.get_pos()
        tick += 1

        # dimmed background
        screen.blit(bg, (0, 0))
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((20, 28, 48, 175))
        screen.blit(dim, (0, 0))

        # card shadow
        pygame.draw.rect(screen, (90, 90, 90),
                         (card.x+5, card.y+5, CW, CH), border_radius=16)

        # card body
        pygame.draw.rect(screen, CARD, card, border_radius=16)
        pygame.draw.rect(screen, CARD_BDR, card, 2, border_radius=16)

        if page == 0:
            draw_page_0(mouse, tick)
        else:
            draw_page_1(mouse, tick)

        draw_dots(page)
        pygame.display.update()
        clock.tick(60)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if page == 0 and next_r.collidepoint(ev.pos):
                    page = 1
                elif page == 1:
                    if back_r.collidepoint(ev.pos):
                        page = 0
                    elif got_r.collidepoint(ev.pos):
                        return

def screen_slot_picker() -> str | None:
    """
    Display all saved game slots and let the player choose one to load.

    Returns the chosen save file path, or None if the player pressed Back.

    Layout
    ──────
    • Up to MAX_VISIBLE slots shown at once; mouse-wheel / arrow keys scroll.
    • Each row shows: slot number, datetime saved, difficulty, move count,
      a coloured Load button, and a red Delete button.
    • A confirmation pop-up appears before deleting.
    """

    DIFF_NAMES  = {2: "Easy", 3: "Medium", 5: "Hard"}
    DIFF_COLORS = {2: (80, 175, 80), 3: (190, 150, 50), 5: (190, 65, 65)}

    MAX_VISIBLE = 5
    ROW_H       = 68
    CW, CH      = 560, MAX_VISIBLE * ROW_H + 120
    CX, CY      = WIDTH // 2, HEIGHT // 2
    card        = pygame.Rect(CX - CW // 2, CY - CH // 2, CW, CH)

    lbl_f  = pygame.font.SysFont(None, 22)
    body_f = pygame.font.SysFont(None, 26)
    hdr_f  = pygame.font.SysFont(None, 38)
    btn_f  = pygame.font.SysFont(None, 24)

    BACK_RECT = pygame.Rect(card.x + 16, card.bottom - 50, 100, 36)

    def reload():
        return Solution.list_saves(SAVE_DIR)

    def pill(rect, text, clr, hov, mouse, enabled=True):
        c = GRAY if not enabled else (hov if rect.collidepoint(mouse) else clr)
        pygame.draw.rect(screen, c, rect, border_radius=6)
        s = btn_f.render(text, True, (255, 255, 255))
        screen.blit(s, s.get_rect(center=rect.center))

    def confirm_delete(save_info: dict) -> bool:
        """Tiny yes/no overlay. Returns True if user confirms."""
        box   = pygame.Rect(CX - 190, CY - 65, 380, 130)
        yes_r = pygame.Rect(CX - 100, CY + 10, 85, 34)
        no_r  = pygame.Rect(CX + 20,  CY + 10, 85, 34)
        msg   = f"Delete save from {save_info['saved_at']}?"
        while True:
            mouse = pygame.mouse.get_pos()
            pygame.draw.rect(screen, (245, 245, 240), box, border_radius=12)
            pygame.draw.rect(screen, (160, 160, 160), box, 2, border_radius=12)
            ms = lbl_f.render(msg, True, (40, 40, 40))
            screen.blit(ms, ms.get_rect(center=(CX, CY - 25)))
            pill(yes_r, "Delete", (190, 65, 65), (220, 95, 95), mouse)
            pill(no_r,  "Cancel", BLUE,           BLUE_H,        mouse)
            pygame.display.update()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    if yes_r.collidepoint(ev.pos): return True
                    if no_r.collidepoint(ev.pos):  return False

    saves  = reload()
    scroll = 0          # index of first visible row
    bg     = load_bg()

    while True:
        mouse  = pygame.mouse.get_pos()
        saves  = reload()                           # refresh after deletes
        n      = len(saves)
        scroll = max(0, min(scroll, max(0, n - MAX_VISIBLE)))

        # ── background + card ────────────────────────────────────────────────
        screen.blit(bg, (0, 0))
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((20, 28, 48, 170))
        screen.blit(dim, (0, 0))
        pygame.draw.rect(screen, (95, 95, 95), (card.x+4, card.y+4, CW, CH), border_radius=16)
        pygame.draw.rect(screen, (245, 245, 240), card, border_radius=16)
        pygame.draw.rect(screen, (180, 180, 170), card, 2, border_radius=16)

        # ── title ────────────────────────────────────────────────────────────
        ht = hdr_f.render("Continue a Game", True, BLUE)
        screen.blit(ht, (card.x + 20, card.y + 16))
        pygame.draw.line(screen, BLUE,
                         (card.x+20, card.y+50), (card.x+CW-20, card.y+50), 2)

        # ── slot rows ────────────────────────────────────────────────────────
        visible = saves[scroll: scroll + MAX_VISIBLE]
        if not visible:
            ns = body_f.render("No saved games found.", True, (120, 120, 120))
            screen.blit(ns, ns.get_rect(center=(CX, CY - 10)))
        else:
            for i, sv in enumerate(visible):
                ry     = card.y + 60 + i * ROW_H
                row_bg = (235, 240, 250) if i % 2 == 0 else (245, 245, 240)
                pygame.draw.rect(screen, row_bg,
                                 (card.x+10, ry+4, CW-20, ROW_H-6), border_radius=8)

                # slot number badge
                slot_n = scroll + i + 1
                pygame.draw.rect(screen, BLUE,
                                 (card.x+18, ry+14, 28, 28), border_radius=6)
                ns = lbl_f.render(str(slot_n), True, (255,255,255))
                screen.blit(ns, ns.get_rect(center=(card.x+32, ry+28)))

                # datetime + move count
                dt_s = body_f.render(sv["saved_at"], True, (30,30,30))
                mv_s = lbl_f.render(f"{sv['move_count']} moves", True, (100,100,100))
                screen.blit(dt_s, (card.x+58, ry+10))
                screen.blit(mv_s, (card.x+58, ry+34))

                # difficulty badge
                dl   = sv["depth_limit"]
                dc   = DIFF_COLORS.get(dl, GRAY)
                dn   = DIFF_NAMES.get(dl, str(dl))
                pygame.draw.rect(screen, dc, (card.x+240, ry+16, 58, 22), border_radius=5)
                ds   = lbl_f.render(dn, True, (255,255,255))
                screen.blit(ds, ds.get_rect(center=(card.x+269, ry+27)))

                # Load / Delete buttons
                load_r = pygame.Rect(card.x + 318, ry+14, 78, 30)
                del_r  = pygame.Rect(card.x + 406, ry+14, 78, 30)
                pill(load_r, "Load",   BLUE,           BLUE_H,           mouse)
                pill(del_r,  "Delete", (180, 70,  70), (210, 100, 100),  mouse)

                # store rects for hit-testing
                saves[scroll + i]["_load_r"] = load_r
                saves[scroll + i]["_del_r"]  = del_r

        # ── scroll indicators ────────────────────────────────────────────────
        if scroll > 0:
            su = lbl_f.render("^ scroll up", True, (120,120,120))
            screen.blit(su, su.get_rect(center=(CX, card.y + 56)))
        if scroll + MAX_VISIBLE < n:
            sd = lbl_f.render("v scroll down", True, (120,120,120))
            screen.blit(sd, sd.get_rect(center=(CX, card.bottom - 58)))

        # ── back button ──────────────────────────────────────────────────────
        pill(BACK_RECT, "<- Back", AMBER, AMBER_H, mouse)
        pygame.display.update()
        clock.tick(60)

        # ── events ───────────────────────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return None
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    scroll = min(scroll + 1, max(0, n - MAX_VISIBLE))
                if ev.key in (pygame.K_UP, pygame.K_w):
                    scroll = max(0, scroll - 1)
            if ev.type == pygame.MOUSEWHEEL:
                scroll = max(0, min(scroll - ev.y, max(0, n - MAX_VISIBLE)))
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if BACK_RECT.collidepoint(ev.pos):
                    return None
                for sv in saves:
                    if sv.get("_load_r") and sv["_load_r"].collidepoint(ev.pos):
                        return sv["path"]
                    if sv.get("_del_r")  and sv["_del_r"].collidepoint(ev.pos):
                        if confirm_delete(sv):
                            Solution.delete_save(sv["path"])
                        break   # redraw after delete


def screen_intro(can_continue: bool) -> tuple:
    """Return ('new', depth) | ('continue', path)."""
    bg = load_bg()
    while True:
        screen.blit(bg, (0, 0))
        mouse = pygame.mouse.get_pos()
        title = font.render("Tic Tac Toe 9x9", True, TEXT_COLOR)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
        draw_btn(INTRO_NEW_RECT,  "New Game", mouse, BLUE,   BLUE_H)
        draw_btn(INTRO_CONT_RECT, "Continue", mouse, AMBER,  AMBER_H,  enabled=can_continue)
        draw_btn(INTRO_TUT_RECT,  "Tutorial", mouse, PURPLE, PURPLE_H)
        draw_btn(INTRO_EXIT_RECT, "Exit",     mouse, RED_BTN, RED_BTN_H)
        pygame.display.update()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if INTRO_NEW_RECT.collidepoint(ev.pos):
                    depth = screen_difficulty()
                    return "new", depth
                if INTRO_CONT_RECT.collidepoint(ev.pos) and can_continue:
                    chosen = screen_slot_picker()
                    if chosen:                          # player picked a slot
                        return "continue", chosen
                    # else: player pressed Back → stay on intro
                if INTRO_TUT_RECT.collidepoint(ev.pos):
                    screen_tutorial()
                if INTRO_EXIT_RECT.collidepoint(ev.pos):
                    pygame.quit(); sys.exit()


def screen_end(winner_text: str, mouse) -> tuple:
    """Draw end overlay; return (again_rect, home_rect)."""
    box = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 80, 300, 160)
    pygame.draw.rect(screen, (240, 240, 240), box, border_radius=10)
    pygame.draw.rect(screen, (100, 100, 100), box, 3, border_radius=10)
    msg = font.render(winner_text, True, TEXT_COLOR)
    screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 60))
    again = pygame.Rect(WIDTH//2 - 130, HEIGHT//2 + 20, 100, 40)
    home  = pygame.Rect(WIDTH//2 + 30,  HEIGHT//2 + 20, 100, 40)
    draw_btn(again, "Again", mouse, BLUE,  BLUE_H)
    draw_btn(home,  "Home",  mouse, AMBER, AMBER_H)
    return again, home


# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────
def redraw(sol: Solution, status: str):
    bg = load_bg()
    screen.blit(bg, (0, 0))
    draw_grid()
    draw_pieces(sol.state)
    mouse = pygame.mouse.get_pos()
    can_undo  = len(sol._history) > 2 and not sol.is_over and not sol.ai_thinking
    can_redo = len(sol._redo_stack) >= 2 and not sol.ai_thinking
    # draw_status FIRST (clears bottom area), then buttons ON TOP
    draw_status(status, f"Difficulty: {sol.difficulty_name}")
    draw_btn(HOME_RECT,  "Home",  mouse, BLUE,    BLUE_H)
    draw_btn(RESET_RECT, "Reset", mouse, BLUE,    BLUE_H,  enabled=not sol.ai_thinking)
    draw_btn(UNDO_RECT,  "Undo",  mouse, AMBER,   AMBER_H, enabled=can_undo)
    draw_btn(REDO_RECT, "Redo", mouse, PURPLE, PURPLE_H, enabled=can_redo)
    pygame.display.update()


def main():
    sol          = Solution(depth_limit=3)
    show_end     = False
    again_rect   = home_rect = None

    # ── detect existing saves ─────────────────────────────────────────────────
    import os
    os.makedirs(SAVE_DIR, exist_ok=True)
    can_continue = bool(Solution.list_saves(SAVE_DIR))

    choice, payload = screen_intro(can_continue)
    if choice == "new":
        sol.set_difficulty(payload)      # payload = depth
        sol.reset()
    else:
        if not sol.load(payload):        # payload = chosen save path
            sol.reset()

    redraw(sol, "Your turn (X)")

    while True:
        mouse = pygame.mouse.get_pos()

        # ── handle pending AI result ──────────────────────────────────────────
        if not sol.ai_thinking and not show_end:
            new_state = sol.apply_ai_move()
            if new_state is not None:
                prev = sol._history[-2]
                ai_r, ai_c = next(
                    (r, c)
                    for r in range(ROWS)
                    for c in range(COLS)
                    if new_state.grid[r][c] != prev.grid[r][c]
                )
                animate_draw(ai_r, ai_c, "O", new_state, None)
                if sol.is_over:
                    show_end = True
                    if sol.winning_line:
                        animate_line(sol.winning_line, sol.state)
                    redraw(sol, f"{'AI' if sol.winner == 'O' else 'You'} win!")
                else:
                    redraw(sol, "Your turn (X)")

        # ── end overlay ───────────────────────────────────────────────────────
        if show_end:
            label = ("Draw!" if sol.winner == "Draw"
                     else ("You win! 🎉" if sol.winner == "X" else "AI wins!"))
            again_rect, home_rect = screen_end(label, mouse)
            pygame.display.update()

        # ── events ───────────────────────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                sol.save_slot(SAVE_DIR)
                sol.shutdown()
                pygame.quit(); sys.exit()

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    sol.save_slot(SAVE_DIR)
                    pygame.quit()
                    sys.exit()

            if ev.type == pygame.MOUSEBUTTONDOWN:
                pos = ev.pos

                # ── end screen buttons ────────────────────────────────────────
                if show_end:
                    if again_rect and again_rect.collidepoint(pos):
                        sol.reset()
                        show_end = False
                        redraw(sol, "Your turn (X)")
                    elif home_rect and home_rect.collidepoint(pos):
                        sol.save_slot(SAVE_DIR)
                        can_continue = bool(Solution.list_saves(SAVE_DIR))
                        choice, payload = screen_intro(can_continue)
                        if choice == "new":
                            sol.set_difficulty(payload)
                            sol.reset()
                        else:
                            sol.load(payload)
                        show_end = False
                        redraw(sol, "Your turn (X)")
                    continue

                # ── toolbar buttons ───────────────────────────────────────────
                if HOME_RECT.collidepoint(pos):
                    sol.save_slot(SAVE_DIR)
                    can_continue = bool(Solution.list_saves(SAVE_DIR))
                    choice, payload = screen_intro(can_continue)
                    if choice == "new":
                        sol.set_difficulty(payload)
                        sol.reset()
                    else:
                        sol.load(payload)
                    show_end = False
                    redraw(sol, "Your turn (X)")
                    continue

                if RESET_RECT.collidepoint(pos) and not sol.ai_thinking:
                    sol.reset()
                    show_end = False
                    redraw(sol, "Your turn (X)")
                    continue

                if UNDO_RECT.collidepoint(pos):
                    if sol.undo():
                        redraw(sol, "Your turn (X)")
                    continue

                if REDO_RECT.collidepoint(pos):
                    if sol.redo():
                        redraw(sol, "Redo move")
                    continue

                # ── human move ────────────────────────────────────────────────
                x, y = pos
                if y >= HEIGHT - 100 or sol.is_over or sol.ai_thinking:
                    continue
                row, col = y // SQ, x // SQ
                new_state = sol.human_move(row, col)
                if new_state:
                    animate_draw(row, col, "X", new_state, None)
                    if sol.is_over:
                        show_end = True
                        if sol.winning_line:
                            animate_line(sol.winning_line, sol.state)
                        redraw(sol, "You win! 🎉")
                    else:
                        redraw(sol, "AI thinking…")
                        sol.request_ai_move()

        clock.tick(60)


if __name__ == "__main__":
    main()