import pygame, sys, random, math

# ================= 초기화 =================
pygame.init()
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
MAP_WIDTH, MAP_HEIGHT = 4000, 3000  # 훨씬 더 큰 맵
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Among Us AI Smart Crew")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)

# ================= 색상 =================
WHITE, BLACK = (255,255,255), (0,0,0)
RED, GREEN, BLUE, YELLOW = (255,0,0), (0,255,0), (0,0,255), (255,255,0)
GRAY, DARK_GRAY, PURPLE, CYAN = (50,50,50), (30,30,30), (150,0,150), (0,255,255)
ORANGE = (255,165,0)
TAN = (210,180,140)
CORAL = (255,127,80)
MAROON = (128,0,0)
ROSE = (255,192,203)
GOLD = (255,215,0)
BROWN = (139,69,19)
PLAYER_COLOR = BLUE
AI_COLORS = [RED, PURPLE, CYAN, ORANGE, TAN, CORAL, MAROON, ROSE, GOLD, BROWN]
TASK_COLOR = YELLOW

# ================= 클래스 =================
class Player:
    def __init__(self,x,y,color,role="crew",avoid_player=False):
        self.x,self.y,self.color=x,y,color
        self.width,self.height=25,25
        self.role=role
        self.alive=True
        self.ghost=False  # 유령 상태
        self.task_progress=0
        self.target_task=None
        self.venting=False
        self.vent_time=0
        self.avoid_player=avoid_player
        self.fleeing=False
        self.flee_timer=0
        self.flee_target=None
        self.suspect_player=None  # 의심하는 플레이어
        self.wander_target=None  # 임포스터 돌아다니기 목표
    def rect(self):
        return pygame.Rect(self.x,self.y,self.width,self.height)
    def draw(self, camera_x, camera_y):
        if self.alive and not self.venting:
            screen_x = self.x - camera_x
            screen_y = self.y - camera_y
            if -30 < screen_x < SCREEN_WIDTH and -30 < screen_y < SCREEN_HEIGHT:
                pygame.draw.rect(screen, self.color, (screen_x, screen_y, self.width, self.height))
                pygame.draw.rect(screen, WHITE, (screen_x, screen_y, self.width, self.height), 2)
        elif self.ghost and self is player:
            # 플레이어만 유령 상태로 표시
            screen_x = self.x - camera_x
            screen_y = self.y - camera_y
            if -30 < screen_x < SCREEN_WIDTH and -30 < screen_y < SCREEN_HEIGHT:
                # 투명 Surface 생성
                ghost_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                ghost_surface.fill((*self.color, 150))  # 60% 투명
                screen.blit(ghost_surface, (screen_x, screen_y))
                # 테두리
                pygame.draw.rect(screen, (128, 128, 128), (screen_x, screen_y, self.width, self.height), 1)

class Task:
    def __init__(self, x, y, task_type="normal"):
        self.x, self.y = x, y
        self.width, self.height = 25, 25
        self.completed = False
        self.task_type = task_type  # "normal", "fix", "upload"
        self.completion_time = 0  # 미션 완료를 위해 필요한 시간 (프레임)
        self.time_required = {"normal": 120, "fix": 180, "upload": 240}  # 각 타입별 소요 시간
        self.time_needed = self.time_required.get(task_type, 120)
    
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, player, camera_x, camera_y):
        if math.hypot(self.x-player.x, self.y-player.y) < 250:
            screen_x = self.x - camera_x
            screen_y = self.y - camera_y
            if -20 < screen_x < SCREEN_WIDTH and -20 < screen_y < SCREEN_HEIGHT:
                color = TASK_COLOR if not self.completed else GREEN
                pygame.draw.rect(screen, color, (screen_x, screen_y, self.width, self.height))
                pygame.draw.rect(screen, WHITE, (screen_x, screen_y, self.width, self.height), 2)

class Wall:
    def __init__(self,x,y,w,h):
        self.rect=pygame.Rect(x,y,w,h)
    def draw(self, camera_x, camera_y):
        screen_x = self.rect.x - camera_x
        screen_y = self.rect.y - camera_y
        if -self.rect.w < screen_x < SCREEN_WIDTH and -self.rect.h < screen_y < SCREEN_HEIGHT:
            pygame.draw.rect(screen, DARK_GRAY, (screen_x, screen_y, self.rect.w, self.rect.h))

class Body:
    def __init__(self,x,y):
        self.x,self.y=x,y
        self.width,self.height=25,25
    def rect(self):
        return pygame.Rect(self.x,self.y,self.width,self.height)
    def draw(self, player, camera_x, camera_y):
        if math.hypot(self.x-player.x,self.y-player.y)<300:
            screen_x = self.x - camera_x
            screen_y = self.y - camera_y
            if -30 < screen_x < SCREEN_WIDTH and -30 < screen_y < SCREEN_HEIGHT:
                pygame.draw.rect(screen, PURPLE, (screen_x, screen_y, self.width, self.height))

class Vent:
    def __init__(self,x,y,vent_id):
        self.x,self.y=x,y
        self.radius=15
        self.id=vent_id
        self.available_vents=[]
    def rect(self):
        return pygame.Rect(self.x-self.radius,self.y-self.radius,self.radius*2,self.radius*2)
    def draw(self, camera_x, camera_y):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        if -30 < screen_x < SCREEN_WIDTH and -30 < screen_y < SCREEN_HEIGHT:
            pygame.draw.circle(screen, CYAN, (screen_x, screen_y), self.radius)
            pygame.draw.circle(screen, WHITE, (screen_x, screen_y), self.radius, 2)

# ================= 변수 =================
player_role = "imposter" if random.random() < 0.15 else "crew"
player = Player(MAP_WIDTH//2, MAP_HEIGHT//2, PLAYER_COLOR, player_role)

num_ai = 10
ai_roles = ["crew"] * num_ai
if player_role=="crew":
    # 플레이어가 크루면 AI 중 1명만 임포스터
    ai_roles[random.randint(0,num_ai-1)] = "imposter"

positions = [(random.randint(100, MAP_WIDTH-100), random.randint(100, MAP_HEIGHT-100)) for _ in range(num_ai)]
AIs=[]
shuffled_colors = AI_COLORS.copy()
random.shuffle(shuffled_colors)
avoid_ai_idx = random.randint(0, num_ai-1)  # 10분의1 확률로 플레이어를 피할 AI 선택
for i in range(num_ai):
    avoid = (i == avoid_ai_idx)  # 선택된 AI만 회피형
    AIs.append(Player(positions[i][0], positions[i][1], shuffled_colors[i], ai_roles[i], avoid_player=avoid))

# 다양한 미션 타입 생성
task_types = ["normal", "normal", "normal", "fix", "fix", "upload"]
tasks = []
for i in range(25):
    task_type = random.choice(task_types)
    tasks.append(Task(random.randint(100, MAP_WIDTH-100), random.randint(100, MAP_HEIGHT-100), task_type))

# 환기 시스템
vents = [
    Vent(400, 600, 0),
    Vent(MAP_WIDTH-400, 600, 1),
    Vent(400, MAP_HEIGHT-600, 2),
    Vent(MAP_WIDTH-400, MAP_HEIGHT-600, 3),
    Vent(MAP_WIDTH//2, MAP_HEIGHT//2, 4),
]
for i, vent in enumerate(vents):
    vent.available_vents = [v for j, v in enumerate(vents) if i != j]

# ================= 방 / 벽 =================
# 4개의 큰 방을 만들고, 벽의 일부를 파괴해서 문 공간 만들기
walls = [
    # 맵 경계
    Wall(0, 0, MAP_WIDTH, 40),  # 위 경계
    Wall(0, 0, 40, MAP_HEIGHT),  # 왼쪽 경계
    Wall(0, MAP_HEIGHT-40, MAP_WIDTH, 40),  # 아래 경계
    Wall(MAP_WIDTH-40, 0, 40, MAP_HEIGHT),  # 오른쪽 경계
    
    # 중앙 수직 벽 (왼쪽-오른쪽 분리) - 문 공간 비우기
    Wall(MAP_WIDTH//2, 200, 40, 500),  # 위쪽 문 위
    Wall(MAP_WIDTH//2, 800, 40, 500),  # 아래쪽 문 위
    # 문 공간: (MAP_WIDTH//2, 700~800) 상단, (MAP_WIDTH//2, 1400~1500) 하단
    
    # 중앙 수평 벽 (위-아래 분리) - 문 공간 비우기
    Wall(200, MAP_HEIGHT//2, 700, 40),  # 왼쪽 문 왼쪽
    Wall(1100, MAP_HEIGHT//2, 700, 40),  # 왼쪽 문 오른쪽
    # 문 공간: (700~1100, MAP_HEIGHT//2)
    
    # 왼쪽 영역 추가 벽 - 4개 공간으로 나누기
    Wall(300, 300, 500, 40),  # 왼쪽 위 방 아래
    Wall(300, 900, 500, 40),  # 왼쪽 아래 방 위
    
    # 오른쪽 영역 추가 벽 - 4개 공간으로 나누기
    Wall(MAP_WIDTH-800, 300, 500, 40),  # 오른쪽 위 방 아래
    Wall(MAP_WIDTH-800, 900, 500, 40),  # 오른쪽 아래 방 위
    
    # 추가 구역 분리 벽들 (맵이 커졌으므로 더 많은 방 구조)
    Wall(1000, 600, 40, 400),  # 중앙 왼쪽 세로 벽
    Wall(MAP_WIDTH-1040, 600, 40, 400),  # 중앙 오른쪽 세로 벽
    Wall(800, 1500, 600, 40),  # 중앙 아래 가로 벽
]

# Door 클래스는 문은 벽의 일부를 파괴해서 자연스럽게 만들어지므로 불필요

bodies=[]
game_over=False
game_started=False
winner=None
dead_players=[]  # 죽은 플레이어 추적
last_body_count=0  # 시체 개수 변화 감지용

player_speed=5
imposter_range=50
task_range=40
vision_radius=int(min(MAP_WIDTH,MAP_HEIGHT)*0.15)
imposter_kill_cooldown=0
player_kill_cooldown=0
player_kill_count=0  # 플레이어가 킬한 수

# ================= 함수 =================
def check_collision(rect):
    """벽 충돌 감지"""
    for w in walls:
        if rect.colliderect(w.rect):
            return True
    return False

def find_safe_position():
    """벽과 겹치지 않는 안전한 위치 찾기"""
    while True:
        x = random.randint(50, MAP_WIDTH-50)
        y = random.randint(50, MAP_HEIGHT-50)
        test_rect = pygame.Rect(x, y, 25, 25)
        if not check_collision(test_rect):
            return x, y

def can_see_player(observer, target):
    """시야 범위 내에 있는지 확인"""
    return math.hypot(observer.x-target.x, observer.y-target.y) <= vision_radius

def is_path_clear(x1, y1, x2, y2):
    """두 점 사이의 경로가 벽으로 가로막혀 있는지 확인"""
    steps = 20
    for i in range(steps):
        t = i / steps
        check_x = x1 + (x2 - x1) * t
        check_y = y1 + (y2 - y1) * t
        check_rect = pygame.Rect(check_x-2, check_y-2, 4, 4)  # 더 정밀한 확인
        if check_collision(check_rect):
            return False
    return True

def ai_move(ai):
    global imposter_kill_cooldown, player_kill_cooldown, dead_players
    
    if not ai.alive or ai.venting:
        if ai.venting:
            ai.vent_time -= 1
            if ai.vent_time <= 0:
                ai.venting = False
        return
    
    speed = 2.5 if ai.role=="crew" else 3.5

    if ai.role=="imposter":
        # 임포스터 행동
        targets = [p for p in [player]+AIs if p.alive and p.role=="crew"]
        visible_targets = [t for t in targets if can_see_player(ai, t)]  # 시야 내에 있으면 인식 (벽 뒤도)
        
        # 크루가 보이면 추적, 없으면 항상 돌아다니기
        if visible_targets:
            target = visible_targets[0]
            dx, dy = target.x-ai.x, target.y-ai.y
        else:
            # 돌아다니기: 새 목표 설정 또는 기존 목표로 이동
            if ai.wander_target is None or math.hypot(ai.x-ai.wander_target[0], ai.y-ai.wander_target[1]) < 80:
                ai.wander_target = (random.randint(100, MAP_WIDTH-100), random.randint(100, MAP_HEIGHT-100))
            dx = ai.wander_target[0] - ai.x
            dy = ai.wander_target[1] - ai.y
        
        if dx == 0 and dy == 0:
            return
        dist = math.hypot(dx, dy) or 1
        move_x, move_y = dx/dist*speed, dy/dist*speed

        # 목표 방향 시도
        next_rect = pygame.Rect(ai.x+move_x, ai.y+move_y, ai.width, ai.height)
        if not check_collision(next_rect):
            ai.x += move_x
            ai.y += move_y
        else:
            # 벽에 부딪히면 오른쪽→아래 우선으로 빠져나가기
            for alt in [(speed, 0), (0, speed), (-speed, 0), (0, -speed)]:
                alt_rect = pygame.Rect(ai.x+alt[0], ai.y+alt[1], ai.width, ai.height)
                if not check_collision(alt_rect):
                    ai.x += alt[0]
                    ai.y += alt[1]
                    break
        
        if imposter_kill_cooldown <= 0:
            for crew in [p for p in [player]+AIs if p.alive and p.role=="crew"]:
                if math.hypot(ai.x-crew.x, ai.y-crew.y) < imposter_range and is_path_clear(ai.x, ai.y, crew.x, crew.y):
                    crew.alive = False
                    crew.ghost = True  # 유령 상태 활성화
                    if crew is player:
                        print("Player died and became ghost")
                    bodies.append(Body(crew.x, crew.y))
                    dead_players.append(crew)
                    imposter_kill_cooldown = 60
                    break
        
        # 환풍구 자주 이용 (가까우면 높은 확률로 사용)
        for vent in vents:
            if math.hypot(ai.x-vent.x, ai.y-vent.y) < 70:
                if random.random() < 0.08:  # 8% 확률로 환풍구 이용
                    ai.venting = True
                    ai.vent_time = random.randint(20, 50)
                    dest_vent = random.choice(vent.available_vents)
                    ai.x, ai.y = dest_vent.x, dest_vent.y
                    ai.wander_target = None  # 새 위치에서 새 목표 설정
                break
    else:
        # 크루 행동 - 시체/임포환풍 목격시 도망, 평상시 미션
        # 유령은 미션 수행 불가
        if ai.ghost:
            return
        
        # 가끔 의심 리셋 (가끔 잡히게)
        if ai.suspect_player and random.random() < 0.005:
            ai.suspect_player = None
        
        if ai.flee_timer > 0:
            ai.flee_timer -= 1
        
        # 도망 중이면 계속 도망
        if ai.flee_timer > 0 and ai.flee_target:
            dx, dy = ai.flee_target[0] - ai.x, ai.flee_target[1] - ai.y
            dist = math.hypot(dx, dy) or 1
            move_x, move_y = -dx/dist*speed, -dy/dist*speed  # 일반 속도로 도망
            
            # 목표 방향 시도
            next_rect = pygame.Rect(ai.x+move_x, ai.y+move_y, ai.width, ai.height)
            if not check_collision(next_rect):
                ai.x += move_x
                ai.y += move_y
            else:
                # 벽에 부딪히면 오른쪽→아래 우선으로 빠져나가기
                for alt in [(speed, 0), (0, speed), (-speed, 0), (0, -speed)]:
                    alt_rect = pygame.Rect(ai.x+alt[0], ai.y+alt[1], ai.width, ai.height)
                    if not check_collision(alt_rect):
                        ai.x += alt[0]
                        ai.y += alt[1]
                        break
            return
        
        # 도망 원인 확인
        fleeing = False
        flee_target = None
        
        # 플레이어 임포 환풍
        if not fleeing and player.alive and player.venting and player.role == "imposter":
            dist_to_player = math.hypot(ai.x - player.x, ai.y - player.y)
            if dist_to_player < vision_radius and is_path_clear(ai.x, ai.y, player.x, player.y):
                fleeing = True
                flee_target = (player.x, player.y)
                # 환풍 목격 시 의심
                if ai.role == "crew":
                    ai.suspect_player = player
        
        # AI 임포 환풍
        if not fleeing:
            for impostor in [a for a in AIs if a.alive and a.role=="imposter" and a.venting]:
                dist_to_impostor = math.hypot(ai.x - impostor.x, ai.y - impostor.y)
                if dist_to_impostor < vision_radius and is_path_clear(ai.x, ai.y, impostor.x, impostor.y):
                    fleeing = True
                    flee_target = (impostor.x, impostor.y)
                    # 환풍 목격 시 의심
                    if ai.role == "crew":
                        ai.suspect_player = impostor
                    break
        
        # 의심하는 플레이어 피하기
        if not fleeing and ai.suspect_player and ai.suspect_player.alive:
            dist_to_suspect = math.hypot(ai.x - ai.suspect_player.x, ai.y - ai.suspect_player.y)
            if dist_to_suspect < vision_radius:
                fleeing = True
                flee_target = (ai.suspect_player.x, ai.suspect_player.y)
        
        # 도망 시작
        if fleeing and flee_target:
            ai.flee_timer = random.randint(120, 180)
            ai.flee_target = flee_target
            dx, dy = flee_target[0] - ai.x, flee_target[1] - ai.y
            dist = math.hypot(dx, dy) or 1
            move_x, move_y = -dx/dist*speed, -dy/dist*speed  # 일반 속도로 도망
            
            # 목표 방향 시도
            next_rect = pygame.Rect(ai.x+move_x, ai.y+move_y, ai.width, ai.height)
            if not check_collision(next_rect):
                ai.x += move_x
                ai.y += move_y
            else:
                # 벽에 부딪히면 오른쪽→아래 우선으로 빠져나가기
                for alt in [(speed, 0), (0, speed), (-speed, 0), (0, -speed)]:
                    alt_rect = pygame.Rect(ai.x+alt[0], ai.y+alt[1], ai.width, ai.height)
                    if not check_collision(alt_rect):
                        ai.x += alt[0]
                        ai.y += alt[1]
                        break
            return
        
        # 평상시 미션 수행
        if ai.target_task is None or ai.target_task.completed:
            remaining_tasks = [t for t in tasks if not t.completed]
            if remaining_tasks:
                ai.target_task = min(remaining_tasks, key=lambda t: math.hypot(ai.x-t.x, ai.y-t.y))
        
        if ai.target_task:
            dx, dy = ai.target_task.x - ai.x, ai.target_task.y - ai.y
            dist = math.hypot(dx, dy) or 1
            move_x, move_y = dx/dist*speed, dy/dist*speed
            
            # 목표 방향 시도
            next_rect = pygame.Rect(ai.x+move_x, ai.y+move_y, ai.width, ai.height)
            if not check_collision(next_rect):
                ai.x += move_x
                ai.y += move_y
            else:
                # 벽에 부딪히면 오른쪽→아래 우선으로 빠져나가기
                for alt in [(speed, 0), (0, speed), (-speed, 0), (0, -speed)]:
                    alt_rect = pygame.Rect(ai.x+alt[0], ai.y+alt[1], ai.width, ai.height)
                    if not check_collision(alt_rect):
                        ai.x += alt[0]
                        ai.y += alt[1]
                        break
            
            if math.hypot(ai.x-ai.target_task.x, ai.y-ai.target_task.y) < task_range:
                ai.target_task.completed = True

def player_attack():
    global player_kill_cooldown, dead_players, player_kill_count
    
    if player.role=="imposter" and player_kill_cooldown <= 0:
        for crew in [p for p in AIs if p.alive and p.role=="crew"]:
            if math.hypot(player.x-crew.x, player.y-crew.y) < imposter_range and is_path_clear(player.x, player.y, crew.x, crew.y):
                crew.alive = False
                crew.ghost = True  # 유령 상태 활성화
                bodies.append(Body(crew.x, crew.y))
                dead_players.append(crew)
                player_kill_count += 1  # 킬 카운트 증가
                player_kill_cooldown = 60
                break

def player_vent():
    """플레이어 환기"""
    if player.role == "imposter" and not player.venting and player.alive:
        for vent in vents:
            if math.hypot(player.x-vent.x, player.y-vent.y) < 50:  # 50 범위 내
                player.venting = True
                player.vent_time = 30  # 30프레임 동안 환기
                dest_vent = random.choice(vent.available_vents)
                player.x, player.y = dest_vent.x, dest_vent.y
                return True
    return False

def report_body_action():
    """시체 신고 - 시체를 제거하고 게임 상태 변경"""
    for i, b in enumerate(bodies):
        if math.hypot(player.x-b.x, player.y-b.y) < 50:
            bodies.pop(i)  # 신고 후 시체 제거
            print(f"Body reported! Remaining bodies: {len(bodies)}")
            return True
    return False

def check_win():
    global winner, game_over
    alive_crews=[p for p in [player]+AIs if p.alive and p.role=="crew"]
    alive_imposters=[p for p in [player]+AIs if p.alive and p.role=="imposter"]
    
    if alive_imposters and len(alive_crews) == 0:
        winner="Imposters Win!"
        game_over = True
        return True
    if len(alive_imposters) == 0:
        winner="Crew Wins!"
        game_over = True
        return True
    if all(t.completed for t in tasks) and alive_crews:
        winner="Crew Wins! (Tasks Complete)"
        game_over = True
        return True
    return False

def get_camera_pos():
    """플레이어 중심의 카메라 위치"""
    camera_x = player.x - SCREEN_WIDTH // 2
    camera_y = player.y - SCREEN_HEIGHT // 2
    camera_x = max(0, min(camera_x, MAP_WIDTH - SCREEN_WIDTH))
    camera_y = max(0, min(camera_y, MAP_HEIGHT - SCREEN_HEIGHT))
    return camera_x, camera_y

# ================= 게임 루프 =================
game_started = False
# 벽과 겹치지 않는 안전한 위치로 플레이어와 AI 재배치
player.x, player.y = find_safe_position()
for ai in AIs:
    ai.x, ai.y = find_safe_position()

# 타스크 위치 안전하게 재설정
for task in tasks:
    task.x, task.y = find_safe_position()

start_time = pygame.time.get_ticks()

while True:
    screen.fill(GRAY)
    
    # 게임 시작 3초 후 시작
    if not game_started and pygame.time.get_ticks() - start_time > 3000:
        game_started = True
    
    if game_started:
        camera_x, camera_y = get_camera_pos()
    else:
        camera_x, camera_y = MAP_WIDTH//2 - SCREEN_WIDTH//2, MAP_HEIGHT//2 - SCREEN_HEIGHT//2
    
    for event in pygame.event.get():
        if event.type==pygame.QUIT: pygame.quit(); sys.exit()
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE: pygame.quit(); sys.exit()
            if event.key==pygame.K_e and game_started:  # E 키로 환기
                if player.role == "imposter" and player.alive:
                    if player_vent():
                        pass  # 환기 실행됨
            if event.key==pygame.K_r and game_started:  # R 키로 시체 신고
                report_body_action()

    if not game_over and game_started:
        keys=pygame.key.get_pressed()
        dx=dy=0
        if keys[pygame.K_a]: dx=-player_speed
        if keys[pygame.K_d]: dx=player_speed
        if keys[pygame.K_w]: dy=-player_speed
        if keys[pygame.K_s]: dy=player_speed
        
        next_rect = pygame.Rect(player.x+dx, player.y+dy, player.width, player.height)
        if not check_collision(next_rect):
            player.x = max(0, min(player.x+dx, MAP_WIDTH-player.width))
            player.y = max(0, min(player.y+dy, MAP_HEIGHT-player.height))
        else:
            # 벽 방향에 따라 이동 방향 결정
            if abs(dx) > abs(dy):  # 수평 이동 시도 중 (가로 벽)
                alt_directions = [(0, player_speed), (0, -player_speed)]  # 상하 이동
            else:  # 수직 이동 시도 중 (세로 벽)
                alt_directions = [(player_speed, 0), (-player_speed, 0)]  # 좌우 이동
            for alt in alt_directions:
                alt_rect = pygame.Rect(player.x+alt[0], player.y+alt[1], player.width, player.height)
                if not check_collision(alt_rect):
                    player.x = max(0, min(player.x+alt[0], MAP_WIDTH-player.width))
                    player.y = max(0, min(player.y+alt[1], MAP_HEIGHT-player.height))
                    break

        # 플레이어 미션
        for t in tasks:
            if not t.completed and math.hypot(player.x-t.x,player.y-t.y)<task_range and player.role=="crew" and player.alive:
                t.completed=True

        # 플레이어 공격
        if player.alive:
            player_attack()
        
        # 플레이어가 누군가를 죽인 후 감지 (체계적)
        if len(bodies) > last_body_count:
            last_body_count = len(bodies)
            # 새로 추가된 시체 위치
            new_body = bodies[-1]
            # 근처 각 AI가 플레이어를 의심하게 함
            for ai in AIs:
                if ai.alive and ai.role == "crew" and player.alive:
                    dist_to_body = math.hypot(ai.x - new_body.x, ai.y - new_body.y)
                    dist_to_player = math.hypot(ai.x - player.x, ai.y - player.y)
                    # 시체가 300 근처이고 플레이어도 가까우면 의심
                    if dist_to_body < 300 and dist_to_player < 400:
                        ai.suspect_player = player  # 플레이어를 의심
        
        # 플레이어 상태 업데이트
        if player.venting:
            player.vent_time -= 1
            if player.vent_time <= 0:
                player.venting = False

        # AI 이동
        for ai in AIs:
            ai_move(ai)
        
        # 쿨다운 감소
        if imposter_kill_cooldown > 0:
            imposter_kill_cooldown -= 1
        if player_kill_cooldown > 0:
            player_kill_cooldown -= 1

    if check_win():
        pass

    # =============== 화면 그리기 ===============
    for w in walls:
        w.draw(camera_x, camera_y)
    
    for t in tasks:
        t.draw(player, camera_x, camera_y)
    
    for b in bodies:
        b.draw(player, camera_x, camera_y)
    
    for vent in vents:
        vent.draw(camera_x, camera_y)
    
    for p in [player]+AIs:
        if p.alive or p.ghost:
            p.draw(camera_x, camera_y)
    
    # 임포스터 킬 범위 시각화
    if game_started and player.alive and player.role == "imposter":
        player_screen_x = player.x - camera_x + player.width//2
        player_screen_y = player.y - camera_y + player.height//2
        pygame.draw.circle(screen, (255,0,0,100), (player_screen_x, player_screen_y), imposter_range, 1)
    
    # 시야 범위 시각화
    if game_started and player.alive:
        pygame.draw.circle(screen, (50,50,100), (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), vision_radius, 1)

    # =============== HUD 표시 ===============
    if not game_started:
        start_text = font.render("Game Starting...", True, YELLOW)
        role_text = font.render(f"Your Role: {player.role.upper()}", True, CYAN if player.role=="crew" else ORANGE)
        screen.blit(start_text, (SCREEN_WIDTH//2-100, SCREEN_HEIGHT//2-50))
        screen.blit(role_text, (SCREEN_WIDTH//2-150, SCREEN_HEIGHT//2+20))
    else:
        # 기본 정보
        alive_count = sum(1 for p in [player]+AIs if p.alive)
        dead_count = sum(1 for p in [player]+AIs if not p.alive)
        crew_count = sum(1 for p in [player]+AIs if p.alive and p.role=="crew")
        impostor_count = sum(1 for p in [player]+AIs if p.alive and p.role=="imposter")
        
        status_text = font.render(f"Role: {player.role.upper()} | Alive: {alive_count} | Dead: {dead_count}", True, WHITE)
        screen.blit(status_text, (10, 10))
        
        crew_text = font.render(f"Crew: {crew_count} | Impostor: {impostor_count}", True, WHITE)
        screen.blit(crew_text, (10, 40))
        
        tasks_text = font.render(f"Tasks: {sum(1 for t in tasks if t.completed)}/{len(tasks)}", True, WHITE)
        screen.blit(tasks_text, (10, 70))
        
        if player.role == "imposter":
            cooldown_text = font.render(f"Kills: {player_kill_count} | Cooldown: {max(0, player_kill_cooldown//10)}s", True, ORANGE)
            screen.blit(cooldown_text, (10, 100))
        
        if player.venting:
            vent_text = font.render("VENTING...", True, CYAN)
            screen.blit(vent_text, (SCREEN_WIDTH//2-50, SCREEN_HEIGHT//2-100))
        
        # 조작 설명
        controls = [
            "WASD: Move | E: Vent(Imp) | R: Report | ESC: Exit"
        ]
        for i, ctrl in enumerate(controls):
            ctrl_text = font.render(ctrl, True, (100,100,100))
            screen.blit(ctrl_text, (10, SCREEN_HEIGHT-30))

    if game_over:
        win_text = font.render(winner, True, YELLOW)
        win_rect = win_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        pygame.draw.rect(screen, BLACK, win_rect.inflate(40, 40))
        screen.blit(win_text, win_rect)
        
        restart_text = font.render("ESC to Exit", True, WHITE)
        screen.blit(restart_text, (SCREEN_WIDTH//2-100, SCREEN_HEIGHT//2+50))

    pygame.display.flip()
    clock.tick(60)