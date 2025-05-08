import pygame as pg, sys, math, os, random, colorsys, cv2
from abc import abstractmethod, ABCMeta
from typing import Iterator



# TODO: add sprite animation to meteorite
# TODO: make move in and out animation for player, compatible for all ships
# TODO: make powerups compatible with enemies
# TODO: make health bar move at variable speeds



class Game:
    def __init__(self, **kwargs):
        self.running: bool = True
        self.levels: list[Level] = []
        self.screen_w: int = kwargs.get("screen_w", 1400)
        self.screen_h: int = kwargs.get("screen_h", 850)    
        self.screen: pg.Surface = pg.display.set_mode((self.screen_w, self.screen_h))
        self.fps: int = kwargs.get("fps", 60)
        self.clock: pg.time.Clock = pg.time.Clock()

        pg.display.set_caption("Alien Invasion 2")

        self.currentLevel: Level = None
        self.currentLevelIdx: int = 0

        # interface
        self.interface_h: int = kwargs.get("interface_h", 100)
        
        #powerup bars
        self.powerup_grid_position: tuple[int, int] = kwargs.get("powerup_grid_position", (350, self.screen_h - self.interface_h + 10))
       
        self.powerup_icons: dict[Powerup, str | pg.Surface] = kwargs.get("powerup_icons", {})

        #health bar
        self.interface_health_bar_max_w: int = 300
        self.interface_health_bar: pg.Rect = pg.Rect(10, self.screen_h - self.interface_h + 10, self.interface_health_bar_max_w, 80)
        self.interface_health_bar_background: pg.Rect = pg.Rect(10, self.screen_h - self.interface_h + 10, self.interface_health_bar_max_w, 80)
        self.interface_health_bar_color: tuple[int,int,int] = kwargs.get("interface_health_bar_color", None)
        self.powerup_bar_max_w: int = kwargs.get("powerup_bar_max_w", 100)
        self.powerup_bar_h: int = kwargs.get("powerup_bar_h", 25)

        # iterators
        self.draw_player_health_gen: Iterator[None] = None
        self.draw_background_gen: Iterator[None] = None

        self.bg_vid_path: str = "space_background_1.mp4"
        self.bg_vid = cv2.VideoCapture(self.bg_vid_path)

    def check_events(self) -> None:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

    def load_ui_images(self):
        for type, path in self.powerup_icons.items():
            self.powerup_icons[type] = pg.transform.scale(pg.image.load(path), (self.powerup_bar_h, self.powerup_bar_h))

    def start(self) -> None:
        pg.init()
        self.load_ui_images()

        prev_level: Level = None

        while self.running:
            self.check_events()
            # between-level graphics here

            if not self.draw_background_gen:
                self.draw_background_gen = self.draw_background()
            try:
                next(self.draw_background_gen)
            except StopIteration:
                self.draw_background_gen = self.draw_background()

            # intialises level
            # passes on attributes of previous level 
            # e.g., player health & position, active powerups
 
            if self.currentLevelIdx < len(self.levels):
                
                level: Level = self.levels[self.currentLevelIdx](parent=self)

                if prev_level:
                    level.powerups += prev_level.active_powerups
                    level.player.health = prev_level.player.health
                    level.player.rect.y = prev_level.player.rect.y
                    level.meteorites = prev_level.meteorites
                    # level.player.rect.x, level.player.rect.y = pg.mouse.get_pos()

                level.load_sprites()
                level.load_soundfx()
                
                self.currentLevel = level
                
                level.start()

                prev_level = level
                self.currentLevelIdx += 1
                    
            pg.display.flip()
            self.clock.tick(self.fps)
    
    def draw_player_health(self):

        while self.currentLevel.player.health > 0:
 
            pg.draw.rect(self.screen, (0, 0, 0), self.interface_health_bar_background)
            hls = colorsys.hls_to_rgb((self.interface_health_bar.width / self.interface_health_bar_max_w * 100)/360, 0.5, 1)
            
            health_width = self.currentLevel.player.health / self.currentLevel.player.max_health * self.interface_health_bar_max_w

            if self.interface_health_bar.width > health_width:
                self.interface_health_bar.width -= 1
                
            if self.interface_health_bar.width < health_width:
                self.interface_health_bar.width += 1
           
            pg.draw.rect(self.screen, self.interface_health_bar_color or list((i*255 for i in hls)), self.interface_health_bar)

            yield
        yield
    
    def draw_active_powerups(self):
        for idx, powerup in enumerate(self.currentLevel.active_powerups):
            if not powerup.finished:
                # round() rounds to nearest even integer
                column = round((idx + 1) / 2) + 1 if idx == 0 else round((idx + 1) / 2)
                row = int(not idx % 2 == 0)
            
                # first bar's x position + bar's width * by column + a right-margin of 35
                barx = self.powerup_grid_position[0] + (self.powerup_bar_max_w * column) + ((column - 1) * self.powerup_bar_h + 10)
                bary = self.powerup_grid_position[1] + (row * self.powerup_bar_h) + (row * 10)

                self.screen.blit(self.powerup_icons[type(powerup)], self.powerup_icons[type(powerup)].get_rect(top=bary, left=barx - self.powerup_bar_h - 5))
                pg.draw.rect(self.screen, (0, 0, 0), (barx, bary, self.powerup_bar_max_w, self.powerup_bar_h))
                pg.draw.rect(self.screen, (0, 150, 255), (barx, bary, powerup.duration / (powerup.max_duration) * self.powerup_bar_max_w, self.powerup_bar_h))
            
    def draw_interface(self):
        pg.draw.rect(self.screen, (50, 50, 50), (0, self.screen_h - self.interface_h, self.screen_w, self.interface_h))

        # this logic is applied to all generators in the code 
        if not self.draw_player_health_gen:
            self.draw_player_health_gen = self.draw_player_health()
        try:
            next(self.draw_player_health_gen)
        except StopIteration: 
            self.draw_player_health_gen = self.draw_player_health()
       
        self.draw_active_powerups()
    
    def draw_background(self):
        while True:
            vid_read_success, bg_vid_image = self.bg_vid.read()

            if vid_read_success:
                resize = cv2.resize(bg_vid_image, (self.screen_w, self.screen_h)) 
                bg_vid_surface = pg.image.frombuffer(resize.tobytes(), resize.shape[1::-1], "BGR")
            else:
                self.bg_vid = cv2.VideoCapture(self.bg_vid_path)
            self.screen.blit(bg_vid_surface, (0, 0))

            yield

                
class Level:
    def __init__(self, parent: Game, **kwargs):
        self.parent: Game = parent
        self.running: bool = True

        self.player: Player = None
        self.enemy_queue: list[list[StandardEnemy]] = kwargs.get("enemy_queue", [])
        self.enemies: list[StandardEnemy] = kwargs.get("enemies", [])

        self.meteorites: list[Meteorite] = kwargs.get("meteorites", [])
        self.meteorite_spawn_x_position_range: list[int, int] = kwargs.get("meteorite_spawn_x_position_range", [])
        # self.meteorite_angle_range: list[int, int] = kwargs.get("meteorite_angle_range", [])
        self.meteorite_health_range: list[float, float] = kwargs.get("meteorite_health_range", [])
        self.meteorite_vel_range: list[float, float] = kwargs.get("meteorite_vel_range", [])
        self.meteorite_size_range: list[int, int] = kwargs.get("meteorite_size_range", [])
        self.meteorite_damage_range: list[float, float] = kwargs.get("meteorite_damage_range", [])
        self.meteorite_cooldown_range: list[float, float] = kwargs.get("meteorite_cooldown_range", [])

        self.clock = pg.time.Clock()
        self.dt = 0

        self.keys = None

        self.powerup_queue: list[Powerup] = kwargs.get("powerup_queue", [])
        self.powerups: list[Powerup] = kwargs.get("powerups", [])
        self.active_powerups: list[Powerup] = []

        # any new sprite lists are defined here, filled in main.py, and accessed anywhere in this file
        self.sprite_collections: dict[str: list[pg.Surface]] = kwargs.get("sprite_collections", {})

        self.elapsed_time: float = 0

        self.soundfx_collection: dict[str, pg.mixer.Sound] = {}       

    def load_sprites(self) -> None:
        for name, collection in self.sprite_collections.items():
            self.sprite_collections[name] = [pg.image.load(path) for path in collection]

    def load_soundfx(self) -> None:
        pg.mixer.set_num_channels(15)
        for path in self.soundfx_collection:
            self.soundfx_collection[path] = pg.mixer.Sound(self.soundfx_collection[path])
            
    def check_events(self) -> None:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.MOUSEMOTION:
                pg.event.set_grab(True)
            
    def is_rect_onscreen(self, rect: pg.Rect) -> bool:
        if 0 < rect.x < self.parent.screen_w - rect.width and 0 < rect.y < self.parent.screen_h - self.parent.interface_h - rect.height:
            return True
        return False
    
    def handle_enemies(self) -> None:
        if not self.enemies and self.enemy_queue:
            self.enemies = self.enemy_queue.pop(0)

    def handle_powerups(self) -> None:
        # storing new active powerups locally in self.active_powerups 
        for powerup in self.powerup_queue:
            if powerup.cooldown > 0: powerup.cooldown -= self.dt
            if powerup.cooldown <= 0:
                self.powerups.append(powerup)
                self.powerup_queue.remove(powerup)

        for powerup in self.powerups:
            
            if powerup.active and not powerup.finished and powerup not in self.active_powerups:
                self.active_powerups.append(powerup)
            
            if powerup.finished:
                self.active_powerups.remove(powerup)
        
        # finds any stackable powerups and combines their durations into powerup1
        for powerup1 in self.active_powerups:
            if not powerup1.finished:
                for powerup2 in self.active_powerups:
                    if powerup1 != powerup2:
                        if type(powerup1) == type(powerup2):
                                                    
                            powerup1.duration += powerup2.duration
                            powerup1.max_duration = powerup1.duration
                        
                            self.active_powerups.remove(powerup2)
                            self.powerups.remove(powerup2)
            else:
                self.active_powerups.remove(powerup1)
    
    def handle_level_completion(self) -> bool:
        if not self.enemies and not self.enemy_queue:
            if not self.player.move_out_animation_gen:
                self.player.move_out_animation_gen = self.player.move_out_animation()
            try:
                next(self.player.move_out_animation_gen)
            except StopIteration:
                self.player.move_out_animation_gen = self.player.move_out_animation()
        
            if self.player.move_out_anim_finished:
                self.running = False

    def handle_level_start_animations(self):
        if not self.player.move_in_anim_finished:
            if not self.player.move_in_animation_gen:
                self.player.move_in_animation_gen = self.player.move_in_animation()
            try:
                next(self.player.move_in_animation_gen)
            except StopIteration:
                self.player.move_in_animation_gen = self.player.move_in_animation()

    def start(self) -> None:
        
        while self.running:
            
            self.keys = pg.key.get_pressed()
            self.check_events()

            # order of rendering: background > powerups > enemies > player > player bullets > player death anim > enemy bullets > enemy death anim
            if not self.parent.draw_background_gen:
                self.parent.draw_background_gen = self.parent.draw_background()
            try:
                next(self.parent.draw_background_gen)
            except StopIteration:
                self.parent.draw_background_gen = self.parent.draw_background()

            self.handle_powerups()

            for powerup in self.powerups:
                if powerup.rect:
                    powerup.draw()
                    powerup.update_position()
                    powerup.handle_collision()

                if powerup.active:
                    powerup.effect()
                    
                if powerup.finished:
                    self.powerups.remove(powerup)

            for meteorite in self.meteorites:
                if meteorite.is_alive or not meteorite.rect:
                    meteorite.update_position()
                    meteorite.draw()
                    meteorite.handle_collision()
                else:

                    # checks if death_animation_gen variable hasnt been assigned a function
                    if meteorite.death_animation_gen == None:
                        # assigns a function
                        meteorite.death_animation_gen = meteorite.death_animation()
                    # tries to iterate function, if it's exhausted, reassigns fresh function
                    try:
                        next(meteorite.death_animation_gen)
                    except StopIteration: 
                        meteorite.death_animation_gen = meteorite.death_animation()
            
            # iterate through lists in reverse to iterate through every item
            for i in range(len(self.enemies)-1, -1, -1):
                enemy = self.enemies[i]
                
                if enemy.is_alive:
                    enemy.update_position()
                    enemy.draw()
                elif not enemy.rect:
                    self.enemies.remove(enemy)
            
            if not self.enemies:
                self.handle_enemies()

            self.handle_level_start_animations()
            
            if self.player.is_alive:
            
                self.player.draw()
                if self.player.move_in_anim_finished:
                    if not self.player.move_to_cursor_gen:
                        self.player.move_to_cursor_gen = self.player.move_to_cursor()
                    try:
                        next(self.player.move_to_cursor_gen)
                    except StopIteration: 
                        self.player.move_to_cursor_gen = self.player.move_to_cursor()

                if self.is_rect_onscreen(self.player.rect):

                    if not self.player.shoot_gen:
                        self.player.shoot_gen = self.player.shoot()
                    try:
                        next(self.player.shoot_gen)
                    except StopIteration: 
                        self.player.shoot_gen = self.player.shoot()

                if self.player.weapon.rounds:

                    if not self.player.weapon.update_rounds_gen:
                        self.player.weapon.update_rounds_gen = self.player.weapon.update_rounds()
                    try:
                        next(self.player.weapon.update_rounds_gen)
                    except StopIteration: 
                        self.player.weapon.update_rounds_gen = self.player.weapon.update_rounds()

                    self.player.handle_bullet_collision() 
            else:

                if not self.player.death_animation_gen:
                    self.player.death_animation_gen = self.player.death_animation()
                try:
                    next(self.player.death_animation())
                except StopIteration: 
                    self.player.death_animation_gen = self.player.death_animation()
            
            for enemy in self.enemies:
                if enemy.is_alive:

                    if not enemy.shoot_gen:
                        enemy.shoot_gen = enemy.shoot()
                    try:
                        next(enemy.shoot_gen)
                    except StopIteration: 
                        enemy.shoot_gen = enemy.shoot()
                    
                    if not enemy.weapon.update_rounds_gen:
                        enemy.weapon.update_rounds_gen = enemy.weapon.update_rounds()
                    try:
                        next(enemy.weapon.update_rounds_gen)
                    except StopIteration: 
                        enemy.weapon.update_rounds_gen = enemy.weapon.update_rounds()

                    enemy.handle_bullet_collision()
                else:

                    if not enemy.death_animation_gen:
                        enemy.death_animation_gen = enemy.death_animation()
                    try:
                        next(enemy.death_animation_gen)
                    except StopIteration: 
                        enemy.death_animation_gen = enemy.death_animation()
        
            self.parent.draw_interface()
            self.handle_level_completion()
            
            
            pg.display.update()
            self.dt = self.clock.tick(self.parent.fps) / 1000
            self.elapsed_time += self.dt
            # print(self.clock.get_fps())


# for weapons
class Round:
    def __init__(self, currentLevel: Level, parent: object, **kwargs):
        self.parent: Weapon = parent
        self.currentLevel: Level = currentLevel

        self.angle: float = kwargs.get("angle", 90)
        self.prev_angle: float = self.angle
        self.width: int = kwargs.get("width", 8)
        self.height: int = kwargs.get("height", 3)
        self.vel: int = kwargs.get("vel", 10)
        self.color: tuple[int] = kwargs.get("color", (255, 0, 0))

        self.spawn_position: list[int] = kwargs.get("spawn_position", [self.parent.parent.rect.x + self.parent.parent.rect.width, self.parent.parent.rect.y + self.parent.parent.rect.height//2])

        self.is_alive = True

        # death animation
        self.death_sprite_collection_name: str = kwargs.get("death_sprite_collection_name", None)
        self.death_anim_duration = kwargs.get("death_anim_duration", 0.2)
        self.max_death_sprite_frame_duration = self.death_anim_duration / len(self.currentLevel.sprite_collections[self.death_sprite_collection_name])
        self.death_sprite_frame_duration = self.max_death_sprite_frame_duration
        self.death_sprite_frame_index = 0
        self.death_sprite_size: list[int, int] = kwargs.get("death_sprite_size", [35, 35])

        # sprite 
        self.image_path: str = kwargs.get("image_path", "images/Pixel SHMUP Free 1.2/projectile_1.png")
        
        self.image = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_path), self.angle), (self.width, self.height))
        self.rect: pg.Rect = pg.Rect(self.spawn_position[0], self.spawn_position[1], self.width, self.height)
        
        # iterators
        self.death_animation_gen: Iterator[None] = None


    def draw(self):
        if self.angle != self.prev_angle:
            self.image = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_path), self.angle), (self.width, self.height))
            self.prev_angle = self.angle
        self.currentLevel.parent.screen.blit(self.image, self.rect)
    
    def death_animation(self):
        while not self.is_alive and self.rect and self.death_anim_duration > 0:
            while self.death_sprite_frame_duration > 0:
                self.currentLevel.parent.screen.blit(
                    pg.transform.scale(
                        self.currentLevel.sprite_collections[self.death_sprite_collection_name][self.death_sprite_frame_index], 
                        self.death_sprite_size
                    ), 
                    (
                        self.rect.x - self.death_sprite_size[0]//2, 
                        self.rect.y - self.death_sprite_size[1]//2
                    )
                )

                self.death_anim_duration -= self.currentLevel.dt
                self.death_sprite_frame_duration -= self.currentLevel.dt
                yield

            self.death_sprite_frame_index += 1
            self.death_sprite_frame_duration = self.max_death_sprite_frame_duration
            
        self.rect = None

        yield



class Weapon(metaclass=ABCMeta):
    def __init__(self, currentLevel: Level, parent: object=None, **kwargs):
        self.parent: Player = parent
        self.currentLevel = currentLevel

        self.rounds: list[Round] = []
        self.damage: float = kwargs.get("damage", 10)

        self.round_color: tuple = kwargs.get("round_color", (255, 0, 0))
        self.round_size: tuple[int, int] = kwargs.get("round_size", (7, 3))
        self.round_vel: int = kwargs.get("round_vel", 10)

        self.round_death_sprite_collection_name: str = kwargs.get("round_death_sprite_collection_name", None)
        self.round_image_path: str = kwargs.get("round_image_path", "images/Pixel SHMUP Free 1.2/projectile_1.png")
        self.max_shoot_cooldown: float = kwargs.get("max_shoot_cooldown", 0.2)
        self.shoot_cooldown: float = kwargs.get("shoot_cooldown", self.max_shoot_cooldown)

        self.shoot_angle: float = kwargs.get("shoot_angle", 0)

        # iterators
        self.shoot_gen: Iterator[None] = None
        self.update_rounds_gen: Iterator[None] = None

    @abstractmethod
    def shoot(self):
        pass

    # draws and updates round positions
    @abstractmethod
    def update_rounds(self):
        pass



class Weapon1(Weapon):
    def __init__(self, currentLevel: Level, parent: object=None, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

    def shoot(self):
        while True:
      
            if self.shoot_cooldown > 0: self.shoot_cooldown -= self.currentLevel.dt
            if self.shoot_cooldown <= 0:
                round = Round(
                    self.currentLevel, 
                    self, 
                    angle=self.shoot_angle, 
                    spawn_position=[self.parent.rect.x + self.parent.rect.width, self.parent.rect.y + self.parent.rect.height//2], 
                    death_sprite_collection_name=self.round_death_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color,
                    image_path=self.round_image_path
                )
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

                    round.rect.x += right * round.vel
                    round.rect.y += upwards * round.vel

                elif not self.parent.is_alive:
                    round.is_alive = False

                    if not round.death_animation_gen:
                        round.death_animation_gen = round.death_animation()
                    try:
                        next(round.death_animation_gen)
                    except StopIteration: 
                        round.death_animation_gen = round.death_animation()
                
                else:
                    round.is_alive = False

                    if not round.death_animation_gen:
                        round.death_animation_gen = round.death_animation()
                    try:
                        next(round.death_animation_gen)
                    except StopIteration: 
                        round.death_animation_gen = round.death_animation()
                
            yield

        return False



class Weapon2(Weapon1):
    def __init__(self, currentLevel: Level, parent: object=None, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        self.bullet_offset_y = kwargs.get("bullet_offset_y", 10)
        
    def shoot(self):
        while True:

            if self.shoot_cooldown > 0: self.shoot_cooldown -= self.currentLevel.dt
            if self.shoot_cooldown <= 0:
                round1 = Round(
                    self.currentLevel, 
                    self, 
                    angle=self.shoot_angle, 
                    spawn_position=[self.parent.rect.x + self.parent.rect.width, (self.parent.rect.y + self.parent.rect.height//2) + self.bullet_offset_y], 
                    death_sprite_collection_name=self.round_death_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color
                )
                round2 = Round(
                    self.currentLevel,
                    self, 
                    angle=self.shoot_angle,
                    spawn_position=[self.parent.rect.x + self.parent.rect.width, (self.parent.rect.y + self.parent.rect.height//2) - self.bullet_offset_y], 
                    death_sprite_collection_name=self.round_death_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color,
                    image_path=self.round_image_path

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

    def shoot(self):
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
                    spawn_position=[self.parent.rect.x + self.parent.rect.width, (self.parent.rect.y + self.parent.rect.height//2) + self.bullet_offset_y], 
                    death_sprite_collection_name=self.round_death_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color,
                    vel=self.round_vel,
                    image_path=self.round_image_path
                )

                round2 = Round(
                    self.currentLevel, 
                    self, 
                    angle=self.curr_round_angle, 
                    spawn_position=[self.parent.rect.x + self.parent.rect.width, (self.parent.rect.y + self.parent.rect.height//2) - self.bullet_offset_y], 
                    death_sprite_collection_name=self.round_death_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color,
                    vel=self.round_vel,
                    image_path=self.round_image_path
                )

                self.rounds.append(round1)
                self.rounds.append(round2)
                self.shoot_cooldown = self.max_shoot_cooldown

            yield



class Weapon4(Weapon2):
    def __init__(self, currentLevel: Level, parent: object=None, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)
        self.target_enemies: list[Ship] = []
        self.closest_enemy: Ship = None
        self.prev_enemy_dist: float = float("inf")

    def get_closest_enemy_angle(self, round: Round) -> float:
        if not self.closest_enemy or not self.closest_enemy.is_alive: 
            return self.shoot_angle
        adj = self.closest_enemy.rect.x + self.closest_enemy.width/2 - round.rect.x
        opp = self.closest_enemy.rect.y + self.closest_enemy.height/2 - round.rect.y
        hyp = math.sqrt(adj ** 2 + opp ** 2)

        if hyp != 0:
            if opp < 0: 
                return -math.degrees(math.acos(adj / hyp))
            return math.degrees(math.acos(adj / hyp))
        return self.shoot_angle
    
    def shoot(self):
        
        if isinstance(self.parent, Player):
            self.target_enemies = self.currentLevel.enemies
        elif isinstance(self.parent, StandardEnemy):
            self.target_enemies = [self.currentLevel.player]

        if self.closest_enemy is None:
            self.closest_enemy = self.target_enemies[0]

        while True:
            for enemy in self.target_enemies:
                if enemy.rect and (self.parent.rect.x + self.parent.rect.width + 20 < enemy.rect.x or isinstance(self.parent, StandardEnemy) and self.parent.rect.x - 20 > enemy.rect.x):
                    curr_enemy_dist = math.sqrt((self.parent.rect.x - enemy.rect.x)**2 + (self.parent.rect.y - enemy.rect.y)**2)
                    if curr_enemy_dist < self.prev_enemy_dist and self.closest_enemy.is_alive or not self.closest_enemy.is_alive:
                        self.closest_enemy = enemy
                        self.prev_enemy_dist = curr_enemy_dist
                        
            if self.shoot_cooldown > 0: 
                self.shoot_cooldown -= self.currentLevel.dt

            if self.shoot_cooldown <= 0 and self.closest_enemy and self.closest_enemy.is_alive \
                 and ((self.parent.rect.x - 20 > enemy.rect.x and isinstance(self.parent, StandardEnemy)) or (self.parent.rect.x + self.parent.rect.width + 20 < enemy.rect.x and isinstance(self.parent, Player))):
                if isinstance(self.parent, StandardEnemy): print("player", enemy.rect.x, "enemy", self.parent.rect.x)
                round1 = Round(
                    self.currentLevel, 
                    self,
                    spawn_position=[self.parent.rect.x + self.parent.rect.width, (self.parent.rect.y + self.parent.rect.height//2) + self.bullet_offset_y],
                    death_sprite_collection_name=self.round_death_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color,
                    vel=self.round_vel,
                    image_path="images/Pixel SHMUP Free 1.2/projectile_2.png"
                )
                round1.angle = self.get_closest_enemy_angle(round1)

                round2 = Round(
                    self.currentLevel,
                    self, 
                    angle=round1.angle,
                    spawn_position=[self.parent.rect.x + self.parent.rect.width, (self.parent.rect.y + self.parent.rect.height//2) - self.bullet_offset_y], 
                    death_sprite_collection_name=self.round_death_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color,
                    vel=self.round_vel,
                    image_path="images/Pixel SHMUP Free 1.2/projectile_2.png"
                )
                
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

        # health
        self.max_health: float = kwargs.get("max_health", 100)
        self.health: float = self.max_health
        self.immune: bool = kwargs.get("immune", False)

        self.can_shoot: bool = True

        # hit indication
        self.max_hit_indication_duration: float = kwargs.get("max_hit_indication_duration", 0.1)
        self.hit_indication_duration: float = 0
        self.image_hit: pg.Surface = None
        self.hit_indication_audio_name: str = kwargs.get("hit_indication_audio_name", "")

        self.is_alive: bool = True

        # death animation
        self.num_death_explosions: int = kwargs.get("num_death_explosions", 3)

        # total interval time between each explosion
        self.max_death_explosion_interval_time: float = kwargs.get("max_death_explosion_interval_time", 0.1)
        
        self.death_sprite_collection_name: str = kwargs.get("death_sprite_collection_name", None)
        self.death_anim_duration: float = kwargs.get("death_anim_duration", 0.5) + self.max_death_explosion_interval_time
        self.death_sprite_size: list[int, int] = kwargs.get("death_sprite_size", [self.width, self.width])
        
        self.death_explosion_audio_name: str = kwargs.get("death_explosion_audio_name", None)
        # ship sprite
        self.angle = kwargs.get("angle", 270)
        self.image_path: str = kwargs.get("image_path", "images/player/player_ship.png")
        self.image = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_path), self.angle), (self.width, self.height))
        self.rect: pg.Rect = self.image.get_rect(left=self.spawn_position[0], top=self.spawn_position[1])
     
        # hit/damage indication
        self.image_hit_path: str = kwargs.get("image_hit_path", "images/player/player_ship_hit1.png")
        self.image_hit: pg.Surface = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_hit_path), 270), (self.width, self.height))

        # iterators
        self.death_animation_gen: Iterator[None] = None
        self.shoot_gen: Iterator[None] = None
        self.hit_indication_animation_gen: Iterator[None] = None

    @abstractmethod
    def shoot(self, angle: int) -> None:
        pass

    def draw(self) -> None:

        self.currentLevel.parent.screen.blit(self.image, self.rect)

        if self.hit_indication_duration > 0:
            
            if not self.hit_indication_animation_gen:
                self.hit_indication_animation_gen = self.hit_indication_anim() 
            try:
                next(self.hit_indication_animation_gen)
            except StopIteration:
                self.hit_indication_animation_gen = self.hit_indication_anim() 

    @abstractmethod
    def handle_health(self):
        pass

    def take_health(self, amount: float):
        if self.hit_indication_audio_name:
            free_audio_channel = pg.mixer.find_channel()
            if free_audio_channel:
                free_audio_channel.play(self.currentLevel.soundfx_collection[self.hit_indication_audio_name])

        if not self.immune:
            self.health -= amount
        
        if self.health > 0:
            self.hit_indication_duration = self.max_hit_indication_duration
    
    def give_health(self, amount: float):
        self.health = min(self.health + amount, self.max_health)
    
    def hit_indication_anim(self):
        while self.hit_indication_duration:
            self.currentLevel.parent.screen.blit(self.image_hit, self.rect)
            self.hit_indication_duration -= self.currentLevel.dt
            yield

        yield

    def death_animation(self):
        death_explosion_interval_time: float = self.max_death_explosion_interval_time
        max_death_sprite_frame_duration: float = self.death_anim_duration / len(self.currentLevel.sprite_collections[self.death_sprite_collection_name]) 
        death_sprite_frame_duration: float = max_death_sprite_frame_duration
        death_sprite_frame_indexes: list[int] = [0] * self.num_death_explosions
        death_explosion_positions = [[random.randint(-self.width//2, self.width//2), random.randint(-self.height//2, self.height//2)] for _ in range(self.num_death_explosions)]

        self.play_death_audio()
        
        while not self.is_alive and self.rect and self.death_anim_duration > 0:
            while death_sprite_frame_duration > 0:

                for i in range(self.num_death_explosions, 0, -1):
                    if death_explosion_interval_time <= self.max_death_explosion_interval_time * (i / self.num_death_explosions):

                        self.currentLevel.parent.screen.blit(
                            pg.transform.scale(
                                self.currentLevel.sprite_collections[self.death_sprite_collection_name][death_sprite_frame_indexes[self.num_death_explosions - i]], 
                                self.death_sprite_size
                            ), 
                            (
                                self.rect.x + ((self.rect.width - self.death_sprite_size[0])//2) + death_explosion_positions[self.num_death_explosions - i][0], 
                                self.rect.y + ((self.rect.height - self.death_sprite_size[1])//2) + death_explosion_positions[self.num_death_explosions - i][1]
                            )
                        )

                death_explosion_interval_time -= self.currentLevel.dt
                self.death_anim_duration -= self.currentLevel.dt
                death_sprite_frame_duration -= self.currentLevel.dt
                yield

            for i in range(self.num_death_explosions, 0, -1):
                if death_explosion_interval_time <= self.max_death_explosion_interval_time * (i / self.num_death_explosions):
                    death_sprite_frame_indexes[self.num_death_explosions - i] += 1
          
            death_sprite_frame_duration = max_death_sprite_frame_duration

        self.rect = None
        
        yield 

    def play_death_audio(self):
         if self.death_explosion_audio_name:
            free_audio_channel = pg.mixer.find_channel()
            if free_audio_channel:
                free_audio_channel.play(self.currentLevel.soundfx_collection[self.death_explosion_audio_name])
     
        

class Player(Ship):
    def __init__(self, currentLevel: Level, parent: Level, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        self.move_to_cursor_gen: Iterator[None] = None

        self.vel = kwargs.get("vel", 1)

        # iterators
        self.move_out_animation_gen: Iterator[None] = None
        self.move_in_animation_gen: Iterator[None] = None

        self.move_in_anim_finished: bool = False
        self.move_out_anim_finished: bool = True

    def shoot(self):
        while self.can_shoot:
            self.weapon.shoot_cooldown -= self.currentLevel.dt
            if (self.currentLevel.keys[pg.K_SPACE] or pg.mouse.get_pressed()[0]):

                if not self.weapon.shoot_gen:
                    self.weapon.shoot_gen = self.weapon.shoot()
                try:
                    next(self.weapon.shoot_gen)
                except StopIteration:
                    self.weapon.shoot_gen = self.weapon.shoot()

            yield
        yield

    def handle_bullet_collision(self) -> None:
        for round in self.weapon.rounds:
            for enemy in self.currentLevel.enemies + self.currentLevel.meteorites:
                if enemy.is_alive and round.is_alive and round.rect.colliderect(enemy.rect):
                    enemy.take_health(self.weapon.damage)
                    round.is_alive = False
                    enemy.handle_health()
        
        self.weapon.rounds = [r for r in self.weapon.rounds if r.rect is not None]
    
    def handle_health(self):
        if self.health <= 0:
            self.is_alive = False
        
        if self.death_anim_duration <= 0:
            self.rect = None

    def move_to_cursor(self):
        while not self.move_out_animation_gen and self.move_in_anim_finished:
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
        yield

    def move_in_animation(self):
        vel = 1
        self.can_shoot = False

        while self.rect.x < 200:
            if self.rect.x < 100:
                vel += 0.2
            
            if self.rect.x >= 100:
                vel -= 0.
                
            self.rect.x += vel

            yield
        self.move_in_anim_finished = True
        self.can_shoot = True
        yield

    def move_out_animation(self):
        self.immune = True
        self.move_out_anim_finished = False

        vel = -1
        max_vel = -5

        while self.rect.x < self.currentLevel.parent.screen_w:
            if vel > -5:
                self.rect.x += vel
                vel -= 0.2
            
            if vel <= max_vel:
                if max_vel == -5: max_vel = 15

                self.rect.x += vel
                vel += 0.4
            
            yield

        self.immune = False
        self.move_out_anim_finished = True

        yield



class StandardEnemy(Ship):
    def __init__(self, currentLevel: Level, parent: Level, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        # ship sprite
        self.image_path = kwargs.get("image_path", "images/enemy/enemy_ship1.png")
        self.image = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_path), 270), (self.width, self.height))

        self.random_shoot_cooldowns: list[float] = kwargs.get("random_shoot_cooldowns", [1, 1.5, 2, 2.5, 3, 5])
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
    
        # iterators
        self.move_in_animation_gen: Iterator[None] = None

    def shoot(self):
        while self.can_shoot:
            if self.shoot_cooldown is None:
                if self.random_shoot_cooldowns:
                    self.shoot_cooldown = random.choice(self.random_shoot_cooldowns)
                else:
                    self.shoot_cooldown = 1
        
            self.shoot_cooldown -= self.currentLevel.dt
            self.weapon.shoot_cooldown -= self.currentLevel.dt

            if self.shoot_cooldown <= 0 and self.currentLevel.is_rect_onscreen(self.rect):

                if not self.weapon.shoot_gen:
                    self.weapon.shoot_gen = self.weapon.shoot()   
                try:
                    next(self.weapon.shoot_gen)
                except StopIteration:
                    self.weapon.shoot_gen = self.weapon.shoot()   

                self.shoot_cooldown = random.choice(self.random_shoot_cooldowns)

            yield
        
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
        if self.move_in_on_spawn: 
            if not self.move_in_animation_gen:
                self.move_in_animation_gen = self.move_in_anim()
            try:
                next(self.move_in_animation_gen)
            except StopIteration:
                self.move_in_animation_gen = self.move_in_anim()


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

        for enemy in [self.currentLevel.player] + self.currentLevel.meteorites:
            for round in self.weapon.rounds:
                if enemy.is_alive and round.is_alive and round.rect.colliderect(enemy.rect):
                    enemy.take_health(self.weapon.damage)
                    round.is_alive = False
                    enemy.handle_health()



class Powerup:
    def __init__(self, currentLevel: Level, parent: Level, **kwargs):
        self.currentLevel = currentLevel
        self.parent = parent
        self.width: int = kwargs.get("width", 30)
        self.height: int = kwargs.get("height", 30)
        self.spawn_position: list[int, int] = kwargs.get("spawn_position", [100, 100])

        self.vel: float = kwargs.get("vel", 3)

        self.cooldown: float = kwargs.get("cooldown", 2)
        self.duration: float = kwargs.get("duration", 1)
        self.max_duration: float = self.duration
        self.active: bool = kwargs.get("active", False)
        self.finished: bool = False

        # powerup sprite
        self.angle: float = kwargs.get("angle", 0)
        self.image_path: str = kwargs.get("image_path", "images/ui/icon-powerup.png")
        self.image = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_path), self.angle), (self.width, self.height))
        self.rect: pg.Rect = self.image.get_rect(left=self.spawn_position[0], top=self.spawn_position[1])

    def draw(self):
        self.currentLevel.parent.screen.blit(self.image, self.rect)

    def update_position(self):
        self.rect.y += self.vel

    @abstractmethod
    def handle_collision(self):
        pass

    @abstractmethod
    def effect(self):
        pass



class PowerupWeapon(Powerup):
    def __init__(self, currentLevel: Level, parent: Level, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        self.weapon: Weapon = kwargs.get("weapon", Weapon1(currentLevel, parent=None))

    def handle_collision(self):
        if self.currentLevel.player.rect and self.rect.colliderect(self.currentLevel.player.rect):
            self.active = True
            self.rect = None
    
    def effect(self):
        self.currentLevel.player.weapon = self.weapon
        self.weapon.parent = self.currentLevel.player
        self.finished = True 



class PowerupHealth(Powerup):
    def __init__(self, currentLevel: Level, parent: Level, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        self.health_value: float = kwargs.get("health_value", 50)

        self.image_path: str = kwargs.get("image_path", "images/Health & Ammo Pickups/health-green 32px.png")
        self.image = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_path), self.angle), (self.width, self.height))

    def handle_collision(self):
        if self.currentLevel.player.rect and self.rect.colliderect(self.currentLevel.player.rect):
            self.active = True
            self.rect = None
            
    def effect(self):
        self.currentLevel.player.give_health(self.health_value)
        self.finished = True
    


class PowerupShield(Powerup):
    def __init__(self, currentLevel: Level, parent: Level, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        self.image_path: str = kwargs.get("image_path", "images/Health & Ammo Pickups/health-armor 32px.png")
        self.image = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_path), self.angle), (self.width, self.height))

    def handle_collision(self):
        if self.currentLevel.player.rect and self.rect.colliderect(self.currentLevel.player.rect):
            self.active = True
            self.rect = None
    
    def effect(self):
        self.duration -= self.currentLevel.dt

        if not self.currentLevel.player.immune and not self.currentLevel.parent.interface_health_bar_color:
            self.currentLevel.player.immune = True
            self.currentLevel.parent.interface_health_bar_color = (0, 150, 255)

        if self.duration <= 0:
            self.currentLevel.player.immune = False
            self.currentLevel.parent.interface_health_bar_color = None
            self.finished = True



class PowerupDamageBoost(Powerup):
    def __init__(self, currentLevel: Level, parent: Ship=None, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        self.new_damage_value: float = kwargs.get("new_damage_value", 20)

        self.prev_weapon_damage: float = None
        self.prev_round_color: tuple[int,int,int] = None

        self.image_path: str = kwargs.get("image_path", "images/Health & Ammo Pickups/ammo-rifle 32px.png")
        self.image = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_path), self.angle), (self.width, self.height))

    def handle_collision(self):
        
        if self.currentLevel.player.rect and self.rect.colliderect(self.currentLevel.player.rect):
            self.active = True
            self.rect = None
    
    def effect(self):
        self.duration -= self.currentLevel.dt

        if not self.prev_weapon_damage:
            self.prev_weapon_damage = self.currentLevel.player.weapon.damage
        
        if not self.prev_round_color:
            self.prev_round_color = self.currentLevel.player.weapon.round_color

        if self.currentLevel.player.weapon.damage == self.prev_weapon_damage:
            self.currentLevel.player.weapon.damage = self.new_damage_value
            self.currentLevel.player.weapon.round_color = (255, 255, 0)

        if self.duration <= 0:
            self.currentLevel.player.weapon.damage = self.prev_weapon_damage
            self.currentLevel.player.weapon.round_color = self.prev_round_color
            self.finished = True



class Meteorite(Ship):
    def __init__(self, currentLevel: Level, parent: Level, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        self.vel: float = 1
        self.damage: float = 0
        self.passed_screen: bool = True
        self.cooldown: float = 0
        self.spawn_position = [-500, -500]

        self.max_death_anim_duration = self.death_anim_duration
        
        self.image_path = kwargs.get("image_path", "images/meteorite.png")
        self.image = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_path), 270), (self.width, self.height))
        self.rect = self.image.get_rect(left=self.spawn_position[0], top=self.spawn_position[1])

    def shoot(self):
        return
    
    def reset(self):
        self.cooldown = random.randint(*self.currentLevel.meteorite_cooldown_range)
        self.damage = random.randint(*self.currentLevel.meteorite_damage_range)
        self.health = self.max_health = random.randint(*self.currentLevel.meteorite_health_range)
        self.rect.width = self.rect.height = random.randint(*self.currentLevel.meteorite_size_range)
        self.image = pg.transform.scale(self.image, (self.rect.width, self.rect.height))
        self.rect.x = random.randint(*self.currentLevel.meteorite_spawn_x_position_range)
        self.rect.y = random.choice([-150, self.currentLevel.parent.screen_h + 100])
        self.vel = random.randint(*self.currentLevel.meteorite_vel_range)
        self.is_alive = True
        self.death_anim_duration = self.max_death_anim_duration
        self.death_sprite_frame_indexes = [0] * self.num_death_explosions
        self.death_sprite_size = [self.rect.width, self.rect.height]
    
        if self.rect.y > 0:
            self.angle = random.randint(80, 160)
        else:
            self.angle = random.randint(200, 260)

        self.passed_screen = False

    def update_position(self):
        if not self.rect:
            self.rect = self.image.get_rect(left=self.spawn_position[0], top=self.spawn_position[1])
        
        if self.cooldown > 0: self.cooldown -= self.currentLevel.dt

        if self.cooldown <= 0:
            # checks if meteor has appeared on screen
            if not self.passed_screen and self.currentLevel.is_rect_onscreen(self.rect):
                self.passed_screen = True

            # if meteor has previously come on screen and also has now left the screen
            if not self.is_alive or self.passed_screen and not self.currentLevel.is_rect_onscreen(self.rect):
                
                # checks if the meteor is fully off screen before resetting it
                if 0 > self.rect.x + self.rect.width + 10 \
                or self.rect.x - self.rect.width  - 10 > self.currentLevel.parent.screen_w \
                or 0 > self.rect.y + self.rect.height + 10 \
                or self.rect.y - self.rect.width - 10 > self.currentLevel.parent.screen_h: 
                
                    self.reset()
                    
            self.rect.x += math.cos(math.radians(self.angle)) * self.vel
            self.rect.y += -math.sin(math.radians(self.angle)) * self.vel
    
    def handle_health(self):
        if self.health <= 0:
            self.is_alive = False
        
        if self.death_anim_duration <= 0:
            self.rect = None

    def draw(self):
        self.currentLevel.parent.screen.blit(self.image, self.rect)

    def handle_collision(self):

        if self.currentLevel.player.rect and self.rect.colliderect(self.currentLevel.player.rect):
            self.currentLevel.player.take_health(self.damage)
            self.is_alive = False
    
        