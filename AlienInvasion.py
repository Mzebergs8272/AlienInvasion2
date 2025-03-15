import pygame as pg, sys, math, os, random, colorsys, cv2
from abc import abstractmethod, ABCMeta

# TODO: create bullet animations

class Game:
    def __init__(self, **kwargs):
        self.running: bool = True
        self.levels: list[Level] = []
        self.screen_w: int = kwargs.get("screen_w", 1400)
        self.screen_h: int = kwargs.get("screen_h", 750)    
        self.screen: pg.Surface = pg.display.set_mode((self.screen_w, self.screen_h))
        self.fps: int = kwargs.get("fps", 60)
        self.clock: pg.time.Clock = pg.time.Clock()

        pg.display.set_caption("Alien Invasion 2")

        # interface
        self.interface_w: int = kwargs.get("interface_w", 100)
        self.interface_health_bar_max_h = 300

        self.interface_health_bar: pg.Rect = pg.Rect(10, 10, 80, self.interface_health_bar_max_h)
        self.interface_health_bar_background = pg.Rect(10, 10, 80, self.interface_health_bar_max_h)

    def check_events(self) -> None:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

    def start(self) -> None:
        pg.init()
        for level in self.levels:
            while self.running:
                self.check_events()
                # between-level graphics here
                # initialise level here
                
                level.start()

                pg.display.flip()
                self.clock.tick(self.fps)
    
    def draw_player_health(self, health, max_health):
        while health > 0:
            pg.draw.rect(self.screen, (0, 0, 0), self.interface_health_bar_background)
            hls = colorsys.hls_to_rgb((self.interface_health_bar.height / self.interface_health_bar_max_h * 100)/360, 0.5, 1)

            while self.interface_health_bar.height > health / max_health * self.interface_health_bar_max_h:
                self.interface_health_bar.height -= 2
                break
           
            pg.draw.rect(self.screen, list((i*255 for i in hls)), self.interface_health_bar)

            yield
        yield

    def draw_interface(self):
        pg.draw.rect(self.screen, (50, 50, 50), (0, 0, self.interface_w, self.screen_h))
            

                
class Level:
    def __init__(self, parent: Game, **kwargs):
        self.parent: Game = parent
        self.running: bool = True

        self.player: Player = None
        self.enemy_queue: list[list[StandardEnemy]] = kwargs.get("enemy_queue", [])
        self.enemies: list[StandardEnemy] = kwargs.get("enemies", [])

        self.clock = pg.time.Clock()
        self.dt = 0

        self.keys = None
        
        self.bg_vid_url: str = "space_background_1.mp4"
        self.bg_vid = cv2.VideoCapture(self.bg_vid_url)
        self.bg_vid.set(3, 10)
        self.bg_vid.set(4,10)
        self.bg_vid_fps = self.bg_vid.get(cv2.CAP_PROP_FPS)

        # pg.mouse.set_visible(False)

        # any new sprite lists are defined here, filled in main.py, and accessed anywhere in this file
        self.sprite_collections: dict[str: list[pg.Surface]] = kwargs.get("sprite_collections", {})
                                                                
        self.load_sprites()

    def load_sprites(self):
        for name, collection in self.sprite_collections.items():
            self.sprite_collections[name] = [pg.image.load(path) for path in collection]

    def check_events(self) -> None:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.MOUSEMOTION:
                pg.event.set_grab(True)
            
    def is_rect_onscreen(self, rect: pg.Rect) -> bool:
        if self.parent.interface_w < rect.x < self.parent.screen_w - rect.width and 0 < rect.y < self.parent.screen_h - rect.height:
            return True
        return False
    
    def handle_enemies(self) -> None:
        if not self.enemies and self.enemy_queue:
            self.enemies = self.enemy_queue.pop()

    def start(self) -> None:
        while self.running:
            self.keys = pg.key.get_pressed()
            self.check_events()

            self.parent.screen.fill("black")

            success, bg_vid_image = self.bg_vid.read()

            if success:
                resize = cv2.resize(bg_vid_image, (self.parent.screen_w, self.parent.screen_h)) 
                bg_vid_surface = pg.image.frombuffer(resize.tobytes(), resize.shape[1::-1], "BGR")
            else:
                self.bg_vid = cv2.VideoCapture(self.bg_vid_url)
            self.parent.screen.blit(bg_vid_surface, (0, 0))

            # order of rendering: enemies > player > player bullets > player death anim > enemy bullets > enemy death anim
            
            for enemy in self.enemies: 
                if enemy.is_alive:
                    enemy.update_position()
                    enemy.draw()
                elif not enemy.rect:
                    self.enemies.remove(enemy)
            
            if not self.enemies:
                self.handle_enemies()

            if self.player.is_alive:
                self.player.draw()

                next(self.player.move_to_cursor())
                if self.is_rect_onscreen(self.player.rect): next(self.player.shoot())
                next(self.player.weapon.update_rounds())
                self.player.handle_bullet_collision() 
            else:
                next(self.player.death_animation())
            
            for enemy in self.enemies:
             
                if enemy.is_alive:
                    next(enemy.shoot())
                    next(enemy.weapon.update_rounds())
                    enemy.handle_bullet_collision()
                else:
                    next(enemy.death_animation())

            self.parent.draw_interface()
            next(self.parent.draw_player_health(self.player.health, self.player.max_health))
            

            pg.display.update()
            self.dt = self.clock.tick(self.parent.fps) / 1000


# for weapons
class Round:
    def __init__(self, currentLevel: Level, parent: object, **kwargs):
        self.parent: Weapon = parent
        self.currentLevel: Level = currentLevel

        self.angle: float = kwargs.get("angle", 90)
        self.width: int = kwargs.get("width", 7)
        self.height: int = kwargs.get("height", 5)
        self.vel: int = kwargs.get("vel", 10)
        self.color: tuple[int] = kwargs.get("color", (255, 0, 0))

        self.spawn_position: list[int] = kwargs.get("spawn_position", [self.parent.parent.rect.x + self.parent.parent.rect.width, self.parent.parent.rect.y + self.parent.parent.rect.height//2])
        self.rect: pg.Rect = pg.Rect(self.spawn_position[0], self.spawn_position[1], self.width, self.height)

        self.is_alive = True

        # death animation
        self.sprite_collection_name: str = kwargs.get("sprite_collection_name", None)
        self.sprite_collection: list[pg.Surface] = self.currentLevel.sprite_collections.get(self.sprite_collection_name)
        self.death_anim_duration = kwargs.get("death_anim_duration", 0.2)
        self.max_sprite_frame_duration = self.death_anim_duration / len(self.sprite_collection)
        self.sprite_frame_duration = self.max_sprite_frame_duration
        self.sprite_frame_index = 0
        self.sprite_size: list[int, int] = kwargs.get("sprite_size", [35, 35])
    
    def draw(self):
        pg.draw.rect(self.currentLevel.parent.screen, self.color, self.rect)
    
    def death_animation(self):
        if not isinstance(self.sprite_collection[0], pg.Surface): 
            self.sprite_collection = self.parent.parent.parent.sprite_collections["explosion1"]
        while not self.is_alive and self.rect and self.death_anim_duration > 0:
            while self.sprite_frame_duration > 0:
                self.currentLevel.parent.screen.blit(
                    pg.transform.scale(
                        self.sprite_collection[self.sprite_frame_index], 
                        self.sprite_size
                    ), 
                    (
                        self.rect.x - self.sprite_size[0]//2, 
                        self.rect.y - self.sprite_size[1]//2
                    )
                )

                self.death_anim_duration -= self.currentLevel.dt
                self.sprite_frame_duration -= self.currentLevel.dt
                yield

            self.sprite_frame_index += 1
            self.sprite_frame_duration = self.max_sprite_frame_duration
            
        self.rect = None

        yield



class Weapon(metaclass=ABCMeta):
    def __init__(self, currentLevel: Level, parent: object=None, **kwargs):
        self.parent: Player = parent
        self.currentLevel = currentLevel

        self.rounds: list[Round] = []
        self.damage: float = kwargs.get("damage", 10)

        self.round_color: tuple = kwargs.get("round_color", (255, 0, 0))
        self.round_size: tuple[int, int] = kwargs.get("round_size", (7, 5))
        self.round_vel: int = kwargs.get("round_vel", 10)

        self.round_sprite_collection_name: str = kwargs.get("round_sprite_collection_name", None)

        self.max_shoot_cooldown: float = kwargs.get("max_shoot_cooldown", 0.2)
        self.shoot_cooldown: float = kwargs.get("shoot_cooldown", self.max_shoot_cooldown)

        self.shoot_angle: float = kwargs.get("shoot_angle", 0)

        

    @abstractmethod
    def shoot(self, round_spawn_position: list[int, int]):
        pass

    # draws and updates round positions
    @abstractmethod
    def update_rounds(self):
        pass



class Weapon1(Weapon):
    def __init__(self, currentLevel: Level, parent: object=None, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

    def shoot(self, round_spawn_position: list[int, int]):
        while True:
            
            if self.shoot_cooldown > 0: self.shoot_cooldown -= self.currentLevel.dt
            if self.shoot_cooldown <= 0:
                round = Round(
                    self.currentLevel, 
                    self, angle=self.shoot_angle, 
                    spawn_position=round_spawn_position, 
                    sprite_collection_name=self.round_sprite_collection_name
                )
                round.rect.width = self.round_size[0]
                round.rect.height = self.round_size[1]
                round.color = self.round_color
                self.rounds.append(round)
                self.shoot_cooldown = self.max_shoot_cooldown

            yield

    def update_rounds(self):
        
        while self.rounds:
            self.rounds = [r for r in self.rounds if r.rect is not None]
            
            for round in self.rounds:
                if round.is_alive and self.currentLevel.is_rect_onscreen(round.rect):
                    round.draw()
                    
                    upwards = math.sin(math.radians(round.angle))
                    right = math.cos(math.radians(round.angle))

                    if isinstance(self.parent, Player):
                        print(round.angle)
                        print(upwards, right)
                    
                    round.rect.x += right * round.vel
                    round.rect.y += upwards * round.vel
                else:
                    round.is_alive = False
                    next(round.death_animation())

            yield

        yield



class Weapon2(Weapon1):
    def __init__(self, currentLevel: Level, parent: object=None, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        self.bullet_offset_y = kwargs.get("bullet_offset_y", 10)
        
    def shoot(self, round_spawn_position: list[int, int]):
        while True:

            if self.shoot_cooldown > 0: self.shoot_cooldown -= self.currentLevel.dt
            if self.shoot_cooldown <= 0:
                round1 = Round(
                    self.currentLevel, 
                    self, 
                    angle=self.shoot_angle, 
                    spawn_position=[round_spawn_position[0], round_spawn_position[1] + self.bullet_offset_y], 
                    sprite_collection_name=self.round_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color
                )
                round2 = Round(
                    self.currentLevel,
                    self, 
                    angle=self.shoot_angle,
                    spawn_position=[round_spawn_position[0], round_spawn_position[1] - self.bullet_offset_y], 
                    sprite_collection_name=self.round_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color
                )
            
                self.rounds.append(round1)
                self.rounds.append(round2)
                self.shoot_cooldown = self.max_shoot_cooldown

            yield
        
   

class Weapon3(Weapon2):
    def __init__(self, currentLevel: Level, parent: object=None, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        self.curr_round_angle: float = None

        self.upper_bound_offset: float = kwargs.get("max_upper_bound", 30)
        self.lower_bound_offset: float = kwargs.get("max_lower_bound", 30)
       
        self.rotation_speed: float = kwargs.get("rotation_speed", 2)

        self.switch: bool = True

    def shoot(self, round_spawn_position: list[int, int]):
        while True:

            if self.curr_round_angle is None:
                self.curr_round_angle = self.shoot_angle
                self.upper_bound_offset = self.shoot_angle - self.upper_bound_offset
                self.lower_bound_offset = self.shoot_angle + self.lower_bound_offset
            

            if self.switch:
                if self.curr_round_angle > self.upper_bound_offset:
                    self.curr_round_angle -= self.rotation_speed
                else:
                    self.switch = False

            if not self.switch:
                if self.curr_round_angle < self.lower_bound_offset:
                    self.curr_round_angle += self.rotation_speed
                else:
                    self.switch = True

            if self.shoot_cooldown > 0: self.shoot_cooldown -= self.currentLevel.dt
            if self.shoot_cooldown <= 0:

                round1 = Round(
                    self.currentLevel, 
                    self, 
                    angle=self.curr_round_angle, 
                    spawn_position=[round_spawn_position[0], round_spawn_position[1] + self.bullet_offset_y], 
                    sprite_collection_name=self.round_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color,
                    vel=self.round_vel
                )

                round2 = Round(
                    self.currentLevel, 
                    self, 
                    angle=self.curr_round_angle, 
                    spawn_position=[round_spawn_position[0], round_spawn_position[1] - self.bullet_offset_y], 
                    sprite_collection_name=self.round_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color,
                    vel=self.round_vel
                )

                self.rounds.append(round1)
                self.rounds.append(round2)
                self.shoot_cooldown = self.max_shoot_cooldown

            yield

# TODO: fix closest_enemy logic
# TODO: make compatible with enemies
class Weapon4(Weapon2):
    def __init__(self, currentLevel: Level, parent: object=None, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)
        self.target_enemies: list[Ship] = []
        self.closest_enemy: Ship = None
        self.prev_enemy_dist: float = 9999

    def get_closest_enemy_angle(self, round: Round) -> float:
        adj = self.closest_enemy.rect.x + self.closest_enemy.width//2 - round.rect.x
        opp = self.closest_enemy.rect.y + self.closest_enemy.height//2 - round.rect.y
        hyp = math.sqrt(adj ** 2 + opp ** 2)

        if hyp != 0:
            # print(math.degrees(math.acos(adj / hyp)))
            return math.degrees(math.acos(adj / hyp))
        return self.shoot_angle
    
    def shoot(self, round_spawn_position: list[int, int]):
        
        if isinstance(self.parent, Player):
            self.target_enemies = self.currentLevel.enemies
        elif isinstance(self.parent, StandardEnemy):
            self.target_enemies = [self.currentLevel.player]

        while True:

            if self.closest_enemy is None:
                self.closest_enemy: Ship = self.target_enemies[0]
            
            for enemy in self.target_enemies:
                if self.parent.rect.x + self.parent.rect.width + 20 < enemy.rect.x:
                    curr_enemy_dist = math.sqrt((self.parent.rect.x - enemy.rect.x)**2 + (self.parent.rect.y - enemy.rect.y)**2)
                    if curr_enemy_dist < self.prev_enemy_dist and self.closest_enemy.is_alive or not self.closest_enemy.is_alive:
                        self.closest_enemy = enemy
                        self.prev_enemy_dist = curr_enemy_dist
                        

            if self.shoot_cooldown > 0: self.shoot_cooldown -= self.currentLevel.dt
            if self.shoot_cooldown <= 0:

               

                round1 = Round(
                    self.currentLevel, 
                    self,
                    spawn_position=[round_spawn_position[0], round_spawn_position[1] + self.bullet_offset_y], 
                    sprite_collection_name=self.round_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color
                )
                
                round1.angle = -self.get_closest_enemy_angle(round1)
                print(round1.angle)

                round2 = Round(
                    self.currentLevel,
                    self, 
                    angle=self.shoot_angle,
                    spawn_position=[round_spawn_position[0], round_spawn_position[1] - self.bullet_offset_y], 
                    sprite_collection_name=self.round_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color
                )

                round2.angle = -self.get_closest_enemy_angle(round2)
            
                self.rounds.append(round1)
                self.rounds.append(round2)
                self.shoot_cooldown = self.max_shoot_cooldown

            yield

class Ship(metaclass=ABCMeta):
    def __init__(self, currentLevel: Level, parent: Level, **kwargs):
        self.parent: Level = parent
        self.currentLevel: Level = currentLevel
        self.weapon: Weapon = kwargs.get("weapon", None)

        self.width: int = kwargs.get("width", 100)
        self.height: int = kwargs.get("height", 75)

        self.spawn_position: list[int, int] = kwargs.get("spawn_position", [50, 50])

        #health
        self.max_health: float = kwargs.get("max_health", 100)
        self.health: float = self.max_health

        # hit indication
        self.max_hit_indication_duration: float = kwargs.get("max_hit_indication_duration", 0.1)
        self.hit_indication_duration: float = 0
        self.image_hit: pg.Surface = None

        self.is_alive: bool = True

        # death animation
        self.sprite_collection_name: str = kwargs.get("sprite_collection_name", None)
        self.sprite_collection: list[pg.Surface] = self.parent.sprite_collections.get(self.sprite_collection_name)
        self.death_anim_duration: float = kwargs.get("death_anim_duration", 0.5)
        self.max_sprite_frame_duration: float = self.death_anim_duration / len(self.sprite_collection)
        self.sprite_frame_duration: float = self.max_sprite_frame_duration
        self.sprite_frame_index: int = 0
        self.sprite_size: list[int, int] = kwargs.get("sprite_size", [100, 100])
        
        # ship sprite
        self.angle = kwargs.get("angle", 270)
        self.image_path: str = kwargs.get("image_path", "images/player/player_ship.png")
        self.image = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_path), self.angle), (self.width, self.height))
        self.rect: pg.Rect = self.image.get_rect(left=self.spawn_position[0], top=self.spawn_position[1])
        
        # hit/damage indication
        self.image_hit_path: str = kwargs.get("image_hit_path", "images/player/player_ship_hit1.png")
        self.image_hit: pg.Surface = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_hit_path), 270), (self.width, self.height))

    @abstractmethod
    def shoot(self, angle: int) -> None:
        pass

    def draw(self) -> None:
        self.currentLevel.parent.screen.blit(self.image, self.rect)

        if self.hit_indication_duration > 0:
            next(self.hit_indication_anim())

    @abstractmethod
    def handle_health(self):
        pass

    def take_damage(self, amount: float):
        self.health -= amount
        
        if self.health > 0:
            self.hit_indication_duration = self.max_hit_indication_duration
    
    def hit_indication_anim(self):
        while self.hit_indication_duration:
            self.currentLevel.parent.screen.blit(self.image_hit, self.rect)
            self.hit_indication_duration -= self.currentLevel.dt
            yield

        yield

    def death_animation(self):
        if not isinstance(self.sprite_collection[0], pg.Surface): self.sprite_collection = self.currentLevel.sprite_collections["explosion2"]
        while not self.is_alive and self.rect and self.death_anim_duration > 0:
            while self.sprite_frame_duration > 0:
                self.currentLevel.parent.screen.blit(
                    pg.transform.scale(self.sprite_collection[self.sprite_frame_index], self.sprite_size), (self.rect.x + ((self.rect.width - self.sprite_size[0])//2), self.rect.y + ((self.rect.height - self.sprite_size[1])//2)))

                self.death_anim_duration -= self.currentLevel.dt
                self.sprite_frame_duration -= self.currentLevel.dt
                yield

            self.sprite_frame_index += 1
            self.sprite_frame_duration = self.max_sprite_frame_duration

        self.rect = None

        yield  
        


class Player(Ship):
    def __init__(self, currentLevel: Level, parent: Level, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        self.vel = kwargs.get("vel", 1)
 
    def shoot(self):
        while True:
            self.weapon.shoot_cooldown -= self.currentLevel.dt
            if self.currentLevel.keys[pg.K_SPACE] or pg.mouse.get_pressed()[0]:
                next(self.weapon.shoot([self.rect.x + self.rect.width, self.rect.y + self.rect.height//2]))
            yield

    def handle_bullet_collision(self) -> None:
        for round in self.weapon.rounds:
            for enemy in self.parent.enemies:
                if enemy.is_alive and round.is_alive and round.rect.colliderect(enemy.rect):
                    enemy.take_damage(self.weapon.damage)
                    round.is_alive = False
                    enemy.handle_health()
        
        self.weapon.rounds = [r for r in self.weapon.rounds if r.rect is not None]
    
    def handle_health(self):
        if self.health <= 0:
            self.is_alive = False
        
        if self.death_anim_duration <= 0:
            self.rect = None

    def move_to_cursor(self):
        while True:
            mouse_pos = pg.mouse.get_pos()
            player_pos = [self.rect.x + self.rect.width//2, self.rect.y + self.rect.height//2]
            adj = mouse_pos[0] - player_pos[0]
            opp = mouse_pos[1] - player_pos[1]
            hyp = math.sqrt(adj ** 2 + opp ** 2)

            if hyp != 0:
                sin = opp / hyp
                cos = adj / hyp

                # multiply each ratio by hyp. because the further the cursor (and the longer the hyp), 
                # the faster the ship
                self.rect.x += cos * hyp * 0.35
                self.rect.y += sin * hyp * 0.35
           
            yield



class StandardEnemy(Ship):
    def __init__(self, currentLevel: Level, parent: Level, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        # ship sprite
        self.image_path = kwargs.get("image_path", "images/enemy/enemy_ship1.png")
        self.image = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_path), 270), (self.width, self.height))

        self.random_shoot_cooldowns: list[float] = kwargs.get("random_shoot_cooldowns", [1, 1,5, 2, 2.5, 3])
        self.shoot_cooldown: float = None

        # bounce/wave movement
        self.bounce: bool = kwargs.get("bounce", True)
        self.bounce_speed: float = kwargs.get("bounce_speed", 2) # increment for curr_angle
        self.curr_angle: float = 0 # to get the y ratio
        self.bounce_height: int = kwargs.get("bounce_height", 10) # radius of circle

        # animation on spawn
        self.move_in_on_spawn: bool = kwargs.get("move_in_on_spawn", True)
        self.move_in_vel: float = kwargs.get("move_in_vel", 5)
        self.move_in_offset: int = kwargs.get("move_in_offset", 300)

        # hit/damage indication
        self.image_hit_path = kwargs.get("image_hit_path", "images/enemy/enemy_ship1_hit1.png")
        self.image_hit = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_hit_path), 270), (self.width, self.height))
    
    def shoot(self):
        while True:
            if self.shoot_cooldown is None:
                if self.random_shoot_cooldowns:
                    self.shoot_cooldown = random.choice(self.random_shoot_cooldowns)
                else:
                    self.shoot_cooldown = 1
        
            self.shoot_cooldown -= self.currentLevel.dt
            self.weapon.shoot_cooldown -= self.currentLevel.dt

            if self.shoot_cooldown <= 0 and self.parent.is_rect_onscreen(self.rect):
                next(self.weapon.shoot([self.rect.x, self.rect.y + self.rect.height//2]))
                self.shoot_cooldown = random.choice(self.random_shoot_cooldowns)

            yield

    def move_in_anim(self):
        if self.rect.x == self.spawn_position[0]:
            self.rect.x += self.move_in_offset
        while self.rect.x > self.spawn_position[0]:
            self.rect.x -= self.move_in_vel
        
            if self.rect.x > self.spawn_position[0]:
                yield

        self.move_in_on_spawn = False

        yield

    def update_position(self):
        if self.move_in_on_spawn: next(self.move_in_anim())
            
        if self.bounce:
            # self.rect.x = self.spawn_position[0] + self.bounce_height * math.cos(self.curr_angle)
            self.rect.y = self.spawn_position[1] + self.bounce_height * math.sin(math.radians(self.curr_angle))
            
            self.curr_angle += self.bounce_speed

    def handle_health(self):
        if self.health <= 0:
            self.is_alive = False
        
        if self.death_anim_duration <= 0:
            self.rect = None

    def handle_bullet_collision(self) -> None:
        player = self.parent.player
        for round in self.weapon.rounds:
            if player.is_alive and round.is_alive and round.rect.colliderect(player.rect):
                player.take_damage(self.weapon.damage)
                round.is_alive = False
                player.handle_health()


