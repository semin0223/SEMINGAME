import pygame, sys, random, math, json, os
from pygame.locals import *

RANK_SAVE_FILE = "우주선_등급저장.json"
GAME_TITLE = "20000"

pygame.init()
pygame.mixer.init()

# ================= 화면 =================
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption(GAME_TITLE)
clock = pygame.time.Clock()
FPS = 60

# ================= 색상/폰트 =================
BLACK = (0,0,0)
WHITE = (255,255,255)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,150,255)
YELLOW = (255,255,0)
GRAY = (100,100,100)

font = pygame.font.SysFont("Malgun Gothic", 32)
big_font = pygame.font.SysFont("Malgun Gothic", 80)

# ================= 사운드 =================
pygame.mixer.music.load("배경음.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)
explosion_sound = pygame.mixer.Sound("폭발.mp3")
explosion_sound.set_volume(0.7)

# ================= 플레이어 =================
player_basic_img = pygame.image.load("기본우주선.png").convert_alpha()
player_basic_img = pygame.transform.scale(player_basic_img, (180,180))
player_upgrade_img = pygame.image.load("업그레이드우주선.png").convert_alpha()
player_upgrade_img = pygame.transform.scale(player_upgrade_img, (180,180))

player_img = player_basic_img
player_x = WIDTH//2 - 90
player_y = HEIGHT - 200
player_speed = 9

PLAYER_MAX_HP = 500
player_hp = PLAYER_MAX_HP

# ================= 업그레이드 =================
upgrade_level = 0
MAX_UPGRADE = 5
upgrade_gauge = 0
GAUGE_MAX = 100

# ================= 총알 =================
bullets = []
enemy_bullets = []

# ================= 적 =================
enemy_img = pygame.image.load("적 우주선.png").convert_alpha()
enemy_img = pygame.transform.scale(enemy_img, (70,70))
enemies = []

ENEMY_SPAWN = pygame.USEREVENT + 1
pygame.time.set_timer(ENEMY_SPAWN, 1200)

# ================= 폭발 =================
explosions = []
def create_explosion(x, y):
    explosion_sound.play()
    for _ in range(80):
        explosions.append({
            "x": x, "y": y,
            "dx": random.uniform(-6,6), "dy": random.uniform(-6,6),
            "life": random.randint(30,60),
            "size": random.randint(3,6),
            "color": random.choice([(255,200,0),(255,100,0),(255,255,255)])
        })

# ================= 거리/등급 =================
distance = 0
total_distance = 0
game_over = False
game_clear = False
best_rank_string = "Bronze1"
game_cleared_once = False  # 한 번이라도 플래티넘 클리어했으면 True, 메인 메뉴에 표시

# 보스 처치 여부 (브론즈/실버/골드/플래티넘) — 누적, 파일에 저장
boss_cleared = [False, False, False, False]
# 현재 코스(이번 판)에서만의 처치 — 화면 표시용, 매 게임 리셋
boss_cleared_this_run = [False, False, False, False]

VALID_RANKS = ["Bronze1","Bronze2","Silver1","Silver2","Gold1","Gold2","Platinum1","Platinum2"]

def load_rank_save():
    """저장된 누적 등급·클리어 여부 불러오기"""
    global best_rank_string, boss_cleared, game_cleared_once
    if not os.path.exists(RANK_SAVE_FILE):
        return
    try:
        with open(RANK_SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        loaded_best = data.get("best_rank_string", best_rank_string)
        if loaded_best in VALID_RANKS:
            best_rank_string = loaded_best
        boss_cleared = data.get("boss_cleared", boss_cleared)
        if len(boss_cleared) != 4 or not all(isinstance(c, bool) for c in boss_cleared):
            boss_cleared = [False, False, False, False]
        game_cleared_once = data.get("game_cleared_once", False)
    except (json.JSONDecodeError, IOError):
        pass

def save_rank_save():
    """누적 등급을 파일에 저장"""
    try:
        with open(RANK_SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump({"best_rank_string": best_rank_string, "boss_cleared": boss_cleared, "game_cleared_once": game_cleared_once}, f, ensure_ascii=False)
    except IOError:
        pass

# 게임 시작 시 저장된 누적 등급 로드
load_rank_save()

def get_current_rank():
    """Current run rank for top display"""
    in_boss = boss is not None
    rank_names = ["Bronze", "Silver", "Gold", "Platinum"]
    cleared_count = sum(boss_cleared_this_run)

    if in_boss:
        idx = min(cleared_count, 3)
        return rank_names[idx] + "2"
    else:
        idx = min(cleared_count, 3)
        return rank_names[idx] + "1"

def update_best_rank():
    global best_rank_string
    current = get_current_rank()
    if current not in VALID_RANKS or best_rank_string not in VALID_RANKS:
        return
    if VALID_RANKS.index(current) > VALID_RANKS.index(best_rank_string):
        best_rank_string = current
        save_rank_save()

# ================= 메인 메뉴 =================
def main_menu():
    start_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//3 + 100, 200, 50)
    running_menu = True
    while running_menu:
        screen.fill(BLACK)
        title = big_font.render(GAME_TITLE, True, BLUE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3 - 100))

        rank_text = font.render(f"Best Rank : {best_rank_string}", True, YELLOW)
        screen.blit(rank_text, (WIDTH//2 - rank_text.get_width()//2, HEIGHT//3))

        tip_text = font.render("5% chance: blue bullets heal 30 HP when hit", True, BLUE)
        screen.blit(tip_text, (WIDTH//2 - tip_text.get_width()//2, HEIGHT//3 + 45))

        pygame.draw.rect(screen, BLUE, start_rect)
        start_text = font.render("START", True, WHITE)
        screen.blit(start_text, (start_rect.x + start_rect.width//2 - start_text.get_width()//2,
                                 start_rect.y + start_rect.height//2 - start_text.get_height()//2))

        esc_text = font.render("ESC : Quit", True, WHITE)
        screen.blit(esc_text, (WIDTH//2 - esc_text.get_width()//2, HEIGHT//3 + 180))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                pygame.quit(); sys.exit()
            elif event.type == MOUSEBUTTONDOWN and start_rect.collidepoint(event.pos):
                running_menu = False

# ================= 보스 =================
# 체력 기존 대비 약 15% 증가
boss = None
BOSS_DISTANCE = [3000, 7000, 12000, 20000]
boss_spawned = [False]*4
boss_images = [
    pygame.image.load("브론즈보스.png").convert_alpha(),
    pygame.image.load("실버보스.png").convert_alpha(),
    pygame.image.load("골드보스.png").convert_alpha(),
    pygame.image.load("플래티넘보스.png").convert_alpha()
]

def spawn_boss_by_rank(rank):
    global boss
    base = {"x": WIDTH//2-150, "y": -300, "direction": 1, "speed": 3}
    if rank == "Bronze":
        base.update({"img": boss_images[0], "hp":690, "max_hp":690, "shoot_delay":80, "laser_count":3})
    elif rank == "Silver":
        base.update({"img": boss_images[1], "hp":1035, "max_hp":1035, "shoot_delay":70, "laser_count":4})
    elif rank == "Gold":
        base.update({"img": boss_images[2], "hp":1380, "max_hp":1380, "shoot_delay":60, "laser_count":5})
    elif rank == "Platinum":
        # 1800 → 2070
        base.update({"img": boss_images[3], "hp":2070, "max_hp":2070, "shoot_delay":50, "laser_count":7})
    base["shoot_cd"] = base["shoot_delay"]
    boss = base

def boss_shoot():
    if not boss: return
    boss["shoot_cd"] -= 1
    if boss["shoot_cd"] <= 0:
        mid_x = boss["x"] + 150
        angles_map = {3:[-20,0,20], 4:[-30,-10,10,30], 5:[-40,-20,0,20,40], 7:[-60,-40,-20,0,20,40,60]}
        angles = angles_map.get(boss["laser_count"], [0])
        for a in angles:
            rad = math.radians(a)
            enemy_bullets.append({"x": mid_x, "y": boss["y"]+150, "dx": math.sin(rad)*7, "dy": math.cos(rad)*9, "heal": random.random() < 0.05})
        boss["shoot_cd"] = boss["shoot_delay"]

def update_boss():
    global boss, game_clear
    if not boss: return
    if boss["y"] < 100: boss["y"] += 1
    if boss["x"] <= 0 or boss["x"]+300 >= WIDTH: boss["direction"]*=-1
    boss["x"] += boss["speed"]*boss["direction"]
    screen.blit(boss["img"], (boss["x"], boss["y"]))
    hp_ratio = boss["hp"]/boss["max_hp"]
    pygame.draw.rect(screen, RED, (boss["x"], boss["y"]-12, 300, 10))
    pygame.draw.rect(screen, GREEN, (boss["x"], boss["y"]-12, 300*hp_ratio, 10))
    boss_shoot()
    for b in bullets[:]:
        if boss["x"] < b["x"] < boss["x"]+300 and boss["y"] < b["y"] < boss["y"]+300:
            boss["hp"] -= 20
            try: bullets.remove(b)
            except ValueError: pass
            if boss["hp"] <= 0:
                create_explosion(boss["x"]+150, boss["y"]+150)
                # 현재 코스 + 누적 기록 (누적은 저장)
                for i, img in enumerate(boss_images):
                    if boss["img"] == img:
                        boss_cleared_this_run[i] = True
                        boss_cleared[i] = True
                        save_rank_save()
                        if i == 3:  # 플래티넘 보스 처치 → 게임 클리어
                            game_clear = True
                        break
                boss = None
                break

def check_boss_spawn():
    global boss
    for i, dist in enumerate(BOSS_DISTANCE):
        if distance >= dist and not boss_spawned[i]:
            rank_map = ["Bronze","Silver","Gold","Platinum"]
            spawn_boss_by_rank(rank_map[i])
            boss_spawned[i] = True
            break

# ================= 적/플레이어 =================
def spawn_enemy():
    if not boss:
        enemies.append({"x": random.randint(50, WIDTH-120), "y": -80, "hp":60, "max_hp":60})

def shoot_player():
    center = player_x+90
    angles = []
    if upgrade_level==0: angles=[0]
    elif upgrade_level==1: angles=[-10,0,10]
    elif upgrade_level==2: angles=[-15,-5,5,15]
    elif upgrade_level==3: angles=[-20,-10,0,10,20]
    else: angles=[-30,-20,-10,0,10,20,30]
    for a in angles:
        rad=math.radians(a)
        bullets.append({"x":center,"y":player_y,"dx":math.sin(rad)*6,"dy":-math.cos(rad)*12})

def enemy_shoot(e):
    enemy_bullets.append({"x": e["x"]+35, "y": e["y"]+60, "dx":0, "dy":7, "heal": random.random() < 0.05})
    enemy_bullets.append({"x": e["x"]+35, "y": e["y"]+60, "dx":-4, "dy":6, "heal": random.random() < 0.05})
    enemy_bullets.append({"x": e["x"]+35, "y": e["y"]+60, "dx":4, "dy":6, "heal": random.random() < 0.05})

# ================= 게임 초기화 =================
def reset_game():
    global player_x, player_y, player_hp, bullets, enemy_bullets, enemies, boss
    global upgrade_level, upgrade_gauge, distance, player_img, game_over, game_clear
    global boss_spawned, boss_cleared_this_run

    player_x = WIDTH//2 - 90
    player_y = HEIGHT - 200
    player_hp = PLAYER_MAX_HP
    bullets.clear()
    enemy_bullets.clear()
    enemies.clear()
    boss = None
    upgrade_level = 0
    upgrade_gauge = 0
    player_img = player_basic_img
    distance = 0
    game_over = False
    game_clear = False
    boss_spawned = [False]*4
    boss_cleared_this_run = [False, False, False, False]  # 현재 코스만 리셋
    # best_rank_string, boss_cleared 는 누적 — 초기화하지 않음 (삭제할 때만 저장 파일 삭제)

# ================= 게임 오버 =================
def draw_game_over():
    global total_distance
    total_distance += distance
    screen.fill((10,10,10))
    t = big_font.render("GAME OVER", True, RED)
    screen.blit(t,(WIDTH//2-t.get_width()//2,HEIGHT//3))

    d = font.render(f"Distance : {int(distance)} m", True, WHITE)
    rank_text = font.render(f"Best Rank : {best_rank_string}", True, BLUE)

    r = font.render("R : Restart", True, GREEN)
    m = font.render("M : Main Menu", True, GREEN)
    q = font.render("ESC : Quit", True, WHITE)

    screen.blit(d,(WIDTH//2-d.get_width()//2,HEIGHT//3+120))
    screen.blit(rank_text,(WIDTH//2-rank_text.get_width()//2, HEIGHT//3+160))
    screen.blit(r,(WIDTH//2-r.get_width()//2,HEIGHT//3+220))
    screen.blit(m,(WIDTH//2-m.get_width()//2,HEIGHT//3+260))
    screen.blit(q,(WIDTH//2-q.get_width()//2,HEIGHT//3+300))
    pygame.display.update()

# ================= 게임 클리어 =================
def draw_game_clear():
    screen.fill((10,10,30))
    t = big_font.render("GAME CLEAR", True, YELLOW)
    screen.blit(t,(WIDTH//2-t.get_width()//2,HEIGHT//3-40))
    sub = font.render("Platinum Boss Defeated!", True, BLUE)
    screen.blit(sub,(WIDTH//2-sub.get_width()//2,HEIGHT//3+40))
    rank_clear_text = font.render("Rank Cleared!", True, GREEN)
    screen.blit(rank_clear_text,(WIDTH//2-rank_clear_text.get_width()//2,HEIGHT//3+80))
    d = font.render(f"Distance : {int(distance)} m", True, WHITE)
    rank_text = font.render(f"Best Rank : {best_rank_string}", True, BLUE)
    r = font.render("R : Restart", True, GREEN)
    m = font.render("M : Main Menu", True, GREEN)
    q = font.render("ESC : Quit", True, WHITE)
    screen.blit(d,(WIDTH//2-d.get_width()//2,HEIGHT//3+130))
    screen.blit(rank_text,(WIDTH//2-rank_text.get_width()//2, HEIGHT//3+170))
    screen.blit(r,(WIDTH//2-r.get_width()//2,HEIGHT//3+230))
    screen.blit(m,(WIDTH//2-m.get_width()//2,HEIGHT//3+270))
    screen.blit(q,(WIDTH//2-q.get_width()//2,HEIGHT//3+310))
    pygame.display.update()

# ================= 게임 루프 =================
main_menu()
reset_game()
running = True
shoot_cd = 0
stars = [{"x":random.randint(0,WIDTH), "y":random.randint(0,HEIGHT), "s":random.randint(1,3)} for _ in range(120)]

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == QUIT:
            running=False
        elif event.type==KEYDOWN:
            if event.key==K_ESCAPE:
                running=False
            if event.key==K_r and (game_over or game_clear):
                reset_game()
            if event.key==K_m and (game_over or game_clear):
                main_menu(); reset_game()
        elif event.type==ENEMY_SPAWN and not boss and not game_over and not game_clear:
            spawn_enemy()

    keys = pygame.key.get_pressed()
    if not game_over and not game_clear:
        if keys[K_LEFT] and player_x>0: player_x-=player_speed
        if keys[K_RIGHT] and player_x<WIDTH-player_img.get_width(): player_x+=player_speed
        if keys[K_UP] and player_y>0: player_y-=player_speed
        if keys[K_DOWN] and player_y<HEIGHT-player_img.get_height(): player_y+=player_speed
        if keys[K_SPACE] and shoot_cd<=0: shoot_player(); shoot_cd=15

    if shoot_cd>0: shoot_cd-=1

    if not game_over and not game_clear:
        if not boss: distance += 1
        check_boss_spawn()

        for e in enemies[:]:
            e["y"]+=4
            if random.random()<0.01: enemy_shoot(e)
            if e["y"]>HEIGHT:
                try: enemies.remove(e)
                except ValueError: pass

        for b in bullets[:]:
            b["x"]+=b["dx"]; b["y"]+=b["dy"]
            if b["y"]<0 or b["x"]<0 or b["x"]>WIDTH:
                try: bullets.remove(b)
                except ValueError: pass

        for eb in enemy_bullets[:]:
            eb["x"]+=eb["dx"]; eb["y"]+=eb["dy"]
            if eb["y"]>HEIGHT or eb["x"]<0 or eb["x"]>WIDTH:
                try: enemy_bullets.remove(eb)
                except ValueError: pass
                continue
            if player_x<eb["x"]<player_x+180 and player_y<eb["y"]<player_y+180:
                if eb.get("heal"):
                    player_hp = min(player_hp + 30, PLAYER_MAX_HP)  # 회복 탄(파란색) → 체력 30 회복
                else:
                    player_hp -= 10
                try: enemy_bullets.remove(eb)
                except ValueError: pass
                if player_hp<=0: game_over=True

        for e in enemies[:]:
            for b in bullets[:]:
                if e["x"]<b["x"]<e["x"]+70 and e["y"]<b["y"]<e["y"]+70:
                    e["hp"]-=20
                    try: bullets.remove(b)
                    except ValueError: pass
                    if e["hp"]<=0:
                        create_explosion(e["x"]+35,e["y"]+35)
                        try: enemies.remove(e)
                        except ValueError: pass
                        if upgrade_level<MAX_UPGRADE:
                            upgrade_gauge+=20
                            while upgrade_gauge>=GAUGE_MAX and upgrade_level<MAX_UPGRADE:
                                upgrade_level+=1; upgrade_gauge-=GAUGE_MAX
                        else:
                            upgrade_gauge=GAUGE_MAX
                        if upgrade_level>0: player_img=player_upgrade_img

        for ex in explosions[:]:
            ex["x"]+=ex["dx"]; ex["y"]+=ex["dy"]; ex["life"]-=1
            if ex["life"]<=0:
                try: explosions.remove(ex)
                except ValueError: pass

    # --- 화면 그리기 ---
    screen.fill(BLACK)
    for s in stars:
        pygame.draw.circle(screen,WHITE,(s["x"],s["y"]),s["s"])
        s["y"]+=1
        if s["y"]>HEIGHT:
            s["y"]=0; s["x"]=random.randint(0,WIDTH)

    screen.blit(player_img,(player_x,player_y))
    pygame.draw.rect(screen,RED,(player_x,player_y-10,180,10))
    pygame.draw.rect(screen,GREEN,(player_x,player_y-10,180*player_hp/PLAYER_MAX_HP,10))
    pygame.draw.rect(screen,GRAY,(player_x,player_y-22,180,8))
    pygame.draw.rect(screen,BLUE,(player_x,player_y-22,180*upgrade_gauge/GAUGE_MAX,8))

    for e in enemies:
        screen.blit(enemy_img,(e["x"],e["y"]))
        pygame.draw.rect(screen,RED,(e["x"],e["y"]-6,70,6))
        pygame.draw.rect(screen,GREEN,(e["x"],e["y"]-6,70*e["hp"]/e["max_hp"],6))

    for b in bullets: pygame.draw.circle(screen,YELLOW,(int(b["x"]),int(b["y"])),5)
    for eb in enemy_bullets: pygame.draw.circle(screen, BLUE if eb.get("heal") else RED, (int(eb["x"]),int(eb["y"])), 6)
    for ex in explosions: pygame.draw.circle(screen,ex["color"],(int(ex["x"]),int(ex["y"])),ex["size"])

    update_boss()
    update_best_rank()

    # --- 등급/거리 표시 ---
    current_rank_text = font.render(get_current_rank(), True, YELLOW)
    dist_text = font.render(f"Distance: {distance}", True, WHITE)
    screen.blit(dist_text,(20,20))
    screen.blit(current_rank_text,(20,50))

    if game_clear:
        draw_game_clear()
    elif game_over:
        draw_game_over()

    pygame.display.update()

pygame.quit()