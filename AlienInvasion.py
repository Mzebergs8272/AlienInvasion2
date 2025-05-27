import pygame as pg, sys, math, os, random, colorsys, cv2, asyncio, json, time, websockets, threading, timeit
from abc import abstractmethod, ABCMeta
from typing import Iterator
from websockets import WebSocketClientProtocol


# TODO: improve peformance of ship sprite animations
# TODO: make health bar move at variable speeds


# TODO: implement multiplayer
## sub-tasks:

### both players, all ships, meteorites and powerups are placed in dictionaries, instead of lists, with unique IDs
#### this means there will need to be functions to correctly add entities e.g., add_player(), add_enemy(), add_meteorite() inside of Level
#### the IDs of all entities are created in the server.py file and sent to both clients to be applied

### to simulate other player hitting an enemy or meteorite or powerup:

#### create functions in Client to log these actions into player_curr_actions dictionary and implement these actions wherever necessary
##### formats for some of the fields: "damaged_enemies": ["enemy1", "enemy2"]

### to update the attributes of all entities:

#### a function such as "update_entities() -> None" should be implemented:
##### this function will take a dict as input
###### the format of the dictionary should be something like this:
"""
curr_actions = {
    "enemies": 
    {
        "enemy_1": 
        {
            "health": 50
        },
        "enemy_2:
        {
            "health": 20
        }
    }

    "powerups": ["powerup_1"],

    "meteorites": ["meteorite_1"]
    
}

in this frame: the client has dealt damage to enemy_1 and enemy_2, has picked up a powerup and has hit a meteorite.

note: the attribute names e.g., "health", listed in the dict, must be identical to the corresponding ones in the corresponding objects.

the powerups and meteorites will need to be able to interact with both player objects,
so it's required to add arguments to the methods of the powerups e.g., def effect(self, player: Player) so they can be used on command

"""

### to ensure synchronisation of both player's actions, by making all the attributes all entities of both clients the same,
### the initial attributes of all objects need to be shared by the host (the first client to connect to the server).
### this means these attributes need to be configured before the clients' levels start.
### step-by-step this would be like: use a function in Client to grab all the attributes of all entities using .__dict__ 
### and plugging them into a larger dict with a format such as: 
"""
    "enemies": 
    {
        "enemy_1": 
        {
            "spawn_position": 10, 
            "death_sprite_collection_name": "explosion1", 
            "default_sprite_collection_name": "enemy1_default_anim",
            "default_anim_sprite_size": [100, 50],
            "hit_indication_sprite_collection_name": "enemy1_default_anim_hit",
            "width": 50,
            "height": 50,
            "random_shoot_cooldowns": [1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3],
            "angle": 180,
            "rect_offset": [10, 0],
            "death_anim_duration": 0.5,
            "move_in_offset": 900,
            "move_in_from": 1,
            "max_death_explosion_interval_time": 0.15,
            "num_death_explosions": 3,
            "bounce_speed": 2,
            "bounce_height": 7,
            "draw_health": False,
            "bounce_delay": 0,
            "draw_rect": False,
        },
        "enemy_1_weapon": {
            <all attributes of a weapon>
        }


        
    }


attributes that are objects such as currentLevel or parent cannot be shared, so make sure to exclude any of those specific attributes
additionally, the weapons and their attributes of all ships also must be included
note: to easily copy the attributes from the dict to an object use: example_entity.__dict__.update(example_shared_dict)

this operation will be done with a unique function to send and share these attributes and they will be recieved and applied with a unique function
e.g., send_all_entity_attributes() and configure_all_entity_attributes


"""


def time_function(desc: str):
    def decorator(func):
        def wrapper():
            print(f"{desc} took {timeit.timeit(func, number=1)} to run")
        
        return wrapper
    return decorator



class Client:
    def __init__(self, game: object, id: int): 
        self.game: Game = game
        self.id: int = random.randint(0, 100)
        self.server: WebSocketClientProtocol = None
        self.uri: str = "ws://109.147.61.116:8765"

        self.other_player: Player = None
        self.other_player_curr_actions: dict[str, str] = {
            "is_shooting": False,
            "x": 50,
            "y": 50,
        }
        self.client_curr_actions: dict[str, str] = {
            "is_shooting": False,
            "x": 50,
            "y": 50,
        }

    def get_player_data(self) -> dict:
        return

    async def run(self):
        async with websockets.connect(self.uri) as self.server:
            await self.server.send(json.dumps({"id": self.id}))

            while True:
                await self.server.send(json.dumps(self.client_curr_actions))

                other_player_data = await self.server.recv()

                if other_player_data:
                    
                    self.other_player_curr_actions = {
                        "is_shooting": False,
                        "x": 50,
                        "y": 50,
                    }

                    other_player_data: dict[str, int] = json.loads(other_player_data)
                    
                    if not self.other_player:
                        self.second_player = Player(
                            self.game.currentLevel, 
                            self.game.currentLevel,
                            vel=10, 
                            angle=0,
                            width=75,
                            death_sprite_collection_name="explosion1",
                            default_sprite_collection_name="player_default_anim",
                            hit_indication_sprite_collection_name="player_default_anim_hit",
                            spawn_position=[150, 150],
                            max_health=300, 
                            move_in_from=0,
                            move_in_offset=-2500,
                            rect_offset=[50, 0],
                            draw_rect=True,
                            is_other_player=True,
                        )
                

                    self.other_player_curr_actions = other_player_data

                # await asyncio.sleep(0.05) 
           


class Game:
    def __init__(self, **kwargs):
        self.running: bool = True
        self.levels: list[Level] = []
        self.screen_w: int = kwargs.get("screen_w", 1400)
        self.screen_h: int = kwargs.get("screen_h", 850)    
        self.screen: pg.Surface = pg.display.set_mode((self.screen_w, self.screen_h))
        self.fps: int = kwargs.get("fps", 60)
        self.clock: pg.time.Clock = pg.time.Clock()
        self.dt: float = 0

        # self.client: Client = Client(self, 1)

        pg.display.set_caption("Alien Invasion 2")

        self.currentLevel: Level = None
        self.currentLevelIdx: int = 0
        self.can_start: bool = False

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

        self.running_level_interlude: bool = False
        
        # iterators
        self.draw_player_health_gen: Iterator[None] = None
        self.draw_background_gen: Iterator[None] = None
        self.draw_main_menu_gen: Iterator[None] = None
        self.run_levels_gen: Iterator[None] = None
        self.level_interlude_gen: Iterator[None] = None

        self.bg_vid_path: str = "space_background_1.mp4"
        self.bg_vid = cv2.VideoCapture(self.bg_vid_path)

    def check_events(self) -> None:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            
            if (event.type == pg.KEYDOWN or event.type == pg.MOUSEBUTTONDOWN) and not self.can_start:
                self.can_start = True
                self.running_level_interlude = True

    def load_ui_images(self):
        for type, path in self.powerup_icons.items():
            self.powerup_icons[type] = pg.transform.scale(pg.image.load(path), (self.powerup_bar_h, self.powerup_bar_h))

    # intialises level
    # passes on attributes of previous level 
    # e.g., player health & position, active powerups
    def run_levels(self):
        prev_level: Level = None
        while self.currentLevelIdx < len(self.levels):
            if self.can_start:
                    
                level: Level = self.levels[self.currentLevelIdx](parent=self)

                if prev_level:
                    level.powerups += prev_level.active_powerups
                    level.player.health = prev_level.player.health
                    level.player.rect.y = prev_level.player.rect.y
                    level.meteorites = prev_level.meteorites

                level.load_sprites()
                level.load_soundfx()
              
                self.currentLevel = level
                
                level.run()

                prev_level = level
                self.currentLevelIdx += 1
                self.running_level_interlude = True

            yield
        
        yield

    def level_interlude(self):
        vel = 2
        curr_angle = 180

        font = pg.font.Font(None, 70)
        text: pg.Surface = font.render(f"Level {self.currentLevelIdx+1}", True, (255, 255, 255))

        text_rect = text.get_rect()
        text_rect.x = -text_rect.width
        text_rect.y = self.screen_h // 2 - text_rect.height // 2
        
        while text_rect.x <= self.screen_w:
          
            text_rect.x += vel

            if curr_angle > 0:
                text_rect.x = math.cos(math.radians(curr_angle)) * self.screen_w // 2 - text_rect.width // 2
                curr_angle -= vel
                
                # if vel is larger than 0 and text_rect has went through 6.5/16 or 40.625% of the screen horizontally
                if vel - 0.1 > 0 and self.screen_w // 16 * 6.5 <= text_rect.x <= self.screen_w // 2:
                    # decrease vel
                    vel -= 0.1
            elif curr_angle <= 0:
                # if text has went half way through screen, invert ratio to make text continue going right with negative curr_angle
                text_rect.x = self.screen_w - math.cos(math.radians(curr_angle)) * self.screen_w // 2 - text_rect.width // 2
                curr_angle -= vel
                vel += 0.1

            self.screen.blit(text, text_rect)
            yield

        self.running_level_interlude = False
        yield

    def start(self) -> None:
        pg.init()
        self.load_ui_images()

        while self.running:
            self.dt = self.clock.tick(self.fps) / 1000
            self.check_events()
            # between-level graphics here

            if not self.draw_background_gen:
                self.draw_background_gen = self.draw_background()
            try:
                next(self.draw_background_gen)
            except StopIteration:
                self.draw_background_gen = self.draw_background()

            if self.can_start:
                if not self.level_interlude_gen:
                    self.level_interlude_gen = self.level_interlude()
                try:
                    next(self.level_interlude_gen)
                except StopIteration:
                    self.level_interlude_gen = self.level_interlude()
            
            if not self.running_level_interlude:
                if not self.run_levels_gen:
                    self.run_levels_gen = self.run_levels()
                try:
                    next(self.run_levels_gen)
                except StopIteration:
                    self.run_levels_gen = self.run_levels()

            if not self.can_start:
                if not self.draw_main_menu_gen:
                    self.draw_main_menu_gen = self.draw_main_menu()
                try:
                    next(self.draw_main_menu_gen)
                except StopIteration:
                    self.draw_main_menu_gen = self.draw_main_menu()
            
            pg.display.flip()
    
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

    def draw_main_menu(self):
        while True:

            font = pg.font.Font(None, 32)
            text = font.render('Press Any Button to Start', True, (255, 255, 255))
            self.screen.blit(text, text.get_rect(x=self.screen_w//2 - (text.get_width()//2), y=self.screen_h//2 - (text.get_height()//2)))

            yield
                        

                
class Level:
    def __init__(self, parent: Game, **kwargs):
        self.parent: Game = parent
        self.running: bool = True

        self.player: Player = None
        self.enemy_queue: list[list[StandardEnemy]] = kwargs.get("enemy_queue", [])
        self.enemies: list[StandardEnemy] = kwargs.get("enemies", [])

        self.clock = pg.time.Clock()
        self.dt = 0
        self.elapsed_time: float = 0

        self.keys = None

        # meteorite config
        self.meteorites: list[Meteorite] = kwargs.get("meteorites", [])
        self.meteorite_spawn_x_position_range: list[int, int] = kwargs.get("meteorite_spawn_x_position_range", [])
        # self.meteorite_angle_range: list[int, int] = kwargs.get("meteorite_angle_range", [])
        self.meteorite_health_range: list[float, float] = kwargs.get("meteorite_health_range", [])
        self.meteorite_vel_range: list[float, float] = kwargs.get("meteorite_vel_range", [])
        self.meteorite_size_range: list[int, int] = kwargs.get("meteorite_size_range", [])
        self.meteorite_damage_range: list[float, float] = kwargs.get("meteorite_damage_range", [])
        self.meteorite_cooldown_range: list[float, float] = kwargs.get("meteorite_cooldown_range", [])

        # powerups
        self.powerup_queue: list[Powerup] = kwargs.get("powerup_queue", [])
        self.powerups: list[Powerup] = kwargs.get("powerups", [])
        self.active_powerups: list[Powerup] = []

        # any new sprite lists are defined here, filled in main.py, and accessed anywhere in this file
        self.sprite_collections: dict[str: list[pg.Surface]] = kwargs.get("sprite_collections", {})

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

    def is_rect_onscreen(self, rect: pg.Rect, offset: int=0) -> bool:
        if 0 - offset < rect.x < (self.parent.screen_w - rect.width) + offset and 0 - offset < rect.y < (self.parent.screen_h - self.parent.interface_h - rect.height) + offset:
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
    
    def start_async_client(self):
        asyncio.run(self.parent.client.run())

    def start(self):
        thread = threading.Thread(target=self.start_async_client, daemon=True)
        thread.start()
        self.run()

    def run(self):
        while self.running:

            if not self.parent.draw_background_gen:
                self.parent.draw_background_gen = self.parent.draw_background()
            try:
                next(self.parent.draw_background_gen)
            except StopIteration:
                self.parent.draw_background_gen = self.parent.draw_background()

            self.dt = self.clock.tick(self.parent.fps) / 1000
            self.keys = pg.key.get_pressed()
            self.check_events()

            # order of rendering: background > powerups > enemies > player > player bullets > player death anim > enemy bullets > enemy death anim
            
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
           
            if not self.enemies:
                self.handle_enemies()

            for i in range(len(self.enemies)-1, -1, -1):
                enemy = self.enemies[i]
            
                if enemy.is_alive:
                    enemy.update_position()
                    
                    enemy.draw()
                elif not enemy.rect and (enemy.weapon and not enemy.weapon.rounds):
                    self.enemies.remove(enemy)

            self.handle_level_start_animations()

            for player in [self.player]:

                if not player: continue

                if player.is_alive:
                
                    player.draw()
                    if not player.is_other_player:
                        if player.move_in_anim_finished:
                            if not player.move_to_cursor_gen:
                                player.move_to_cursor_gen = player.move_to_cursor()
                            try:
                                next(player.move_to_cursor_gen)
                            except StopIteration: 
                                player.move_to_cursor_gen = player.move_to_cursor()
                            
          
                        
                        if player.draw_health:
                            if not player.draw_health_bar_gen:
                                player.draw_health_bar_gen = player.draw_health_bar()
                            try:
                                next(player.draw_health_bar_gen)
                            except StopIteration:
                                player.draw_health_bar_gen = player.draw_health_bar()
                    
            
                    if self.is_rect_onscreen(player.rect):

                        if not player.shoot_gen:
                            player.shoot_gen = player.shoot()
                        try:
                            # if curr player is client-side or if player is not client-side and is shooting
                            if not player.is_other_player or player.is_other_player:
                                next(player.shoot_gen)
                        except StopIteration: 
                            player.shoot_gen = player.shoot()
                
                    if not player.weapon.update_rounds_gen:
                        player.weapon.update_rounds_gen = player.weapon.update_rounds()
                    try:
                        next(player.weapon.update_rounds_gen)
                    except StopIteration: 
                        player.weapon.update_rounds_gen = player.weapon.update_rounds()

                    if not player.handle_bullet_collision_gen:
                        player.handle_bullet_collision_gen = player.handle_bullet_collision()
                    try:
                        next(player.handle_bullet_collision_gen)
                    except StopIteration:
                        player.handle_bullet_collision_gen = player.handle_bullet_collision()
                        
                else:

                    if not player.death_animation_gen:
                        player.death_animation_gen = player.death_animation()
                    try:
                        next(player.death_animation_gen)
                    except StopIteration: 
                        player.death_animation_gen = player.death_animation()
                
            for enemy in self.enemies:
                if enemy.is_alive:

                    if not enemy.shoot_gen:
                        enemy.shoot_gen = enemy.shoot()
                    try:
                        next(enemy.shoot_gen)
                    except StopIteration: 
                        enemy.shoot_gen = enemy.shoot()
                    
                    if enemy.draw_health:
                        if not enemy.draw_health_bar_gen:
                            enemy.draw_health_bar_gen = enemy.draw_health_bar()
                        try:
                            next(enemy.draw_health_bar_gen)
                        except StopIteration:
                            enemy.draw_health_bar_gen = enemy.draw_health_bar()
                    
                    if not enemy.handle_bullet_collision_gen:
                        enemy.handle_bullet_collision_gen = enemy.handle_bullet_collision()
                    try:
                        next(enemy.handle_bullet_collision_gen)
                    except StopIteration:
                        enemy.handle_bullet_collision_gen = enemy.handle_bullet_collision()

                else: 

                    if not enemy.death_animation_gen:
                        enemy.death_animation_gen = enemy.death_animation()
                    try:
                        next(enemy.death_animation_gen)
                    except StopIteration: 
                        enemy.death_animation_gen = enemy.death_animation()
                
                if not enemy.weapon.update_rounds_gen:
                        enemy.weapon.update_rounds_gen = enemy.weapon.update_rounds()
                try:
                    next(enemy.weapon.update_rounds_gen)
                except StopIteration: 
                    enemy.weapon.update_rounds_gen = enemy.weapon.update_rounds()
        
            self.parent.draw_interface()
            self.handle_level_completion()
            

            pg.display.update()
            self.elapsed_time += self.dt
            print(self.clock.get_fps())

            # time.sleep(self.dt)


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
        self.draw_rect: bool = kwargs.get("draw_rect", False)

        # iterators
        self.death_animation_gen: Iterator[None] = None

    def draw(self):
        if self.draw_rect:
            pg.draw.rect(self.currentLevel.parent.screen, (255, 0, 0), self.rect, 2)

        if self.angle != self.prev_angle:
            self.image = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_path), self.angle-180), (self.width, self.height))
            self.prev_angle = self.angle
        self.currentLevel.parent.screen.blit(self.image, self.rect)
    
    def death_animation(self):
        while not self.is_alive and self.rect and self.death_anim_duration > 0 and self.currentLevel.is_rect_onscreen(self.rect, offset=50):
            while self.death_sprite_frame_duration > 0:

                self.currentLevel.parent.screen.blit(
                    pg.transform.scale(
                        self.currentLevel.sprite_collections[self.death_sprite_collection_name][self.death_sprite_frame_index], 
                        self.death_sprite_size
                    ), 
                    (
                        self.rect.x + self.rect.width//2 + (math.cos(math.radians(self.angle)) * self.rect.width//2) - self.death_sprite_size[0]//2, 
                        self.rect.y + self.rect.height//2 + (math.sin(math.radians(self.angle)) * self.rect.height//2) - self.death_sprite_size[0]//2
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
        self.round_draw_rect: bool = kwargs.get("round_draw_rect", False)

        self.round_death_sprite_collection_name: str = kwargs.get("round_death_sprite_collection_name", None)
        self.round_image_path: str = kwargs.get("round_image_path", "images/Pixel SHMUP Free 1.2/projectile_1.png")
        self.max_shoot_cooldown: float = kwargs.get("max_shoot_cooldown", 0.2)
        self.shoot_cooldown: float = kwargs.get("shoot_cooldown", self.max_shoot_cooldown)
        self.round_spawn_offset: tuple[int, int] = kwargs.get("round_spawn_offset", None)

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
                    spawn_position=[self.parent.rect.x + self.round_spawn_offset[0], self.parent.rect.y + self.round_spawn_offset[1]], 
                    death_sprite_collection_name=self.round_death_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color,
                    vel=self.round_vel,
                    image_path=self.round_image_path,
                    round_draw_rect=self.round_draw_rect,
                )
                self.rounds.append(round)
                self.shoot_cooldown = self.max_shoot_cooldown

            yield

    def update_rounds(self):
        
        while self.rounds:
            self.rounds = [r for r in self.rounds if r.rect is not None]
            
            for round in self.rounds:
                if round.is_alive and self.currentLevel.is_rect_onscreen(round.rect, offset=50):
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
                    spawn_position=[self.parent.rect.x + self.round_spawn_offset[0], self.parent.rect.y + self.round_spawn_offset[1] - self.bullet_offset_y], 
                    death_sprite_collection_name=self.round_death_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color,
                    image_path=self.round_image_path,
                    vel=self.round_vel,
                    round_draw_rect=self.round_draw_rect,
                    
                )
                round2 = Round(
                    self.currentLevel,
                    self, 
                    angle=self.shoot_angle,
                    spawn_position=[self.parent.rect.x + self.round_spawn_offset[0], self.parent.rect.y + self.round_spawn_offset[1] + self.bullet_offset_y], 
                    death_sprite_collection_name=self.round_death_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color,
                    image_path=self.round_image_path,
                    vel=self.round_vel,
                    round_draw_rect=self.round_draw_rect,

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
                    spawn_position=[self.parent.rect.x + self.round_spawn_offset[0], self.parent.rect.y + self.round_spawn_offset[1] - self.bullet_offset_y], 
                    death_sprite_collection_name=self.round_death_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color,
                    vel=self.round_vel,
                    image_path=self.round_image_path,
                    round_draw_rect=self.round_draw_rect,
                )

                round2 = Round(
                    self.currentLevel, 
                    self, 
                    angle=self.curr_round_angle, 
                    spawn_position=[self.parent.rect.x + self.round_spawn_offset[0], self.parent.rect.y + self.round_spawn_offset[1] + self.bullet_offset_y], 
                    death_sprite_collection_name=self.round_death_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color,
                    vel=self.round_vel,
                    image_path=self.round_image_path,
                    round_draw_rect=self.round_draw_rect,
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

        self.angle = 0
        self.offset = 20
        self.osc_speed = 5

    def update_rounds(self):

        while self.rounds:

            self.angle += self.osc_speed

            self.rounds = [r for r in self.rounds if r.rect is not None]
           
            for round in self.rounds:

                if round.is_alive and self.currentLevel.is_rect_onscreen(round.rect, offset=50):
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

        yield

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
                and ((self.parent.rect.x - 20 > self.closest_enemy.rect.x and isinstance(self.parent, StandardEnemy)) or (self.parent.rect.x + self.parent.rect.width + 20 < self.closest_enemy.rect.x and isinstance(self.parent, Player))):
                
                round1 = Round(
                    self.currentLevel, 
                    self,
                    spawn_position=
                    [
                        (self.parent.rect.x + self.round_spawn_offset[0]) + (self.offset * (1-math.cos(math.radians(self.angle)))), 
                        (self.parent.rect.y + self.round_spawn_offset[1] - self.bullet_offset_y) + (self.offset * (1-math.sin(math.radians(self.angle))))
                    ],
                    death_sprite_collection_name=self.round_death_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color,
                    vel=self.round_vel,
                    image_path=self.round_image_path,
                    round_draw_rect=self.round_draw_rect,
                )
                round1.angle = self.get_closest_enemy_angle(round1)

                round2 = Round(
                    self.currentLevel,
                    self, 
                    spawn_position=
                    [
                        (self.parent.rect.x + self.round_spawn_offset[0]) + (self.offset * (1-math.cos(math.radians(self.angle)))), 
                        (self.parent.rect.y + self.round_spawn_offset[1] + self.bullet_offset_y) + (self.offset * (1-math.sin(math.radians(self.angle))))
                    ], 
                    death_sprite_collection_name=self.round_death_sprite_collection_name,
                    width=self.round_size[0],
                    height=self.round_size[1],
                    color=self.round_color,
                    vel=self.round_vel,
                    image_path=self.round_image_path,
                    round_draw_rect=self.round_draw_rect,
                )

                round2.angle = self.get_closest_enemy_angle(round1)
                
                self.rounds.append(round1)
                self.rounds.append(round2)
                self.shoot_cooldown = self.max_shoot_cooldown

            yield



class Weapon5(Weapon1):
    def __init__(self, currentLevel: Level, parent: object=None, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        self.num_rounds: int = kwargs.get("num_rounds", 20)
        self.shoot_radius: int = kwargs.get("shoot_radius", 50)

    def shoot(self):
        alt_angle = 0
        while True:
            
            if self.shoot_cooldown > 0: self.shoot_cooldown -= self.currentLevel.dt
            if self.shoot_cooldown <= 0:

                for i in range(self.num_rounds):
                    round = Round(
                        self.currentLevel, 
                        self, 
                        angle=360 / self.num_rounds * (i+1) + alt_angle, 
                        spawn_position=
                        [
                            (self.parent.rect.x + self.parent.rect.width//2), 
                            (self.parent.rect.y + self.parent.rect.height//2)
                        ], 
                        death_sprite_collection_name=self.round_death_sprite_collection_name,
                        width=self.round_size[0],
                        height=self.round_size[1],
                        color=self.round_color,
                        vel=self.round_vel,
                        image_path=self.round_image_path,
                        round_draw_rect=self.round_draw_rect,

                    )

                    self.rounds.append(round)
                    self.shoot_cooldown = self.max_shoot_cooldown

                    yield

                if self.num_rounds > 0:
                    alt_angle += 360 / self.num_rounds / 4

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
        self.draw_health: bool = kwargs.get("draw_health", False)
        self.is_alive: bool = True
        self.can_shoot: bool = True

        # hit indication
        self.max_hit_indication_duration: float = kwargs.get("max_hit_indication_duration", 0.1)
        self.hit_indication_duration: float = 0
        self.hit_indication_sprite_collection_name: str = kwargs.get("hit_indication_sprite_collection_name", None)
        self.hit_indication_audio_name: str = kwargs.get("hit_indication_audio_name", None)

        self.max_round_comparisons_per_frame: int = kwargs.get("max_round_comparisons_per_frame", 5)

        # death animation
        self.num_death_explosions: int = kwargs.get("num_death_explosions", 3)
        ## total interval time between each explosion
        self.max_death_explosion_interval_time: float = kwargs.get("max_death_explosion_interval_time", 0.1)
        self.death_sprite_collection_name: str = kwargs.get("death_sprite_collection_name", None)
        self.death_anim_duration: float = kwargs.get("death_anim_duration", 0.5) + self.max_death_explosion_interval_time
        self.death_sprite_size: list[int, int] = kwargs.get("death_sprite_size", [self.width, self.width])
        
        self.death_explosion_audio_name: str = kwargs.get("death_explosion_audio_name", None)

        # ship rect
        self.angle = kwargs.get("angle", 270)
        self.rect_offset: tuple[int, int] = kwargs.get("rect_offset", [0, 0])
        self.rect: pg.Rect = pg.Rect(self.spawn_position[0], self.spawn_position[1], self.width, self.height)
        self.draw_rect: bool = kwargs.get("draw_rect", True)
        
        # animation on spawn
        self.move_in_on_spawn: bool = kwargs.get("move_in_on_spawn", True)
        self.move_in_anim_finished: bool = False
        self.move_in_vel: float = kwargs.get("move_in_vel", None)
        self.move_in_offset: int = kwargs.get("move_in_offset", 900)
        ## 0 = left, 1 = right
        self.move_in_from: int = kwargs.get("move_in_from", 1)

        # default sprite animation
        self.default_sprite_collection_name: str = kwargs.get("default_sprite_collection_name", None)
        self.max_default_anim_duration: float = kwargs.get("max_default_anim_duration", 0.5)
        self.default_anim_duration: float = self.max_default_anim_duration
        self.default_anim_sprite_size: tuple[int, int] = kwargs.get("default_anim_sprite_size", [125, 75])

        # iterators
        self.death_animation_gen: Iterator[None] = None
        self.shoot_gen: Iterator[None] = None
        self.hit_indication_animation_gen: Iterator[None] = None
        self.draw_health_bar_gen: Iterator[None] = None
        self.default_animation_gen: Iterator[None] = None
        self.handle_bullet_collision_gen: Iterator[None] = None

    @abstractmethod
    def shoot(self, angle: int) -> None:
        pass

    def draw(self) -> None:
        if self.draw_rect:
            pg.draw.rect(self.currentLevel.parent.screen, (255, 0, 0), self.rect, 2)

        if not self.hit_indication_animation_gen:
            self.hit_indication_animation_gen = self.hit_indication_anim() 
        try:
            next(self.hit_indication_animation_gen)
        except StopIteration:
            self.hit_indication_animation_gen = self.hit_indication_anim() 
        
        if not self.default_animation_gen:
            self.default_animation_gen = self.default_animation()
        try:
            next(self.default_animation_gen)
        except StopIteration:
            self.default_animation_gen = self.default_animation()

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
        prev_default_sprite_collection_name = self.default_sprite_collection_name
        self.default_sprite_collection_name = self.hit_indication_sprite_collection_name

        while self.hit_indication_duration > 0:
            self.hit_indication_duration -= self.currentLevel.dt
            yield

        self.default_sprite_collection_name = prev_default_sprite_collection_name
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
    
    def default_animation(self):
        max_frame_duration = self.default_anim_duration / len(self.currentLevel.sprite_collections[self.default_sprite_collection_name])
        curr_frame_duration = max_frame_duration
        
        while True:
            frame_list_idx = 0
            self.default_anim_duration = self.max_default_anim_duration
            
            while self.default_anim_duration > 0:
                frame_list: list[pg.Surface] = self.currentLevel.sprite_collections[self.default_sprite_collection_name]

                

                while curr_frame_duration > 0:
                    self.currentLevel.parent.screen.blit(pg.transform.scale(pg.transform.rotate(frame_list[frame_list_idx], self.angle-90), self.default_anim_sprite_size), (self.rect.x - self.rect_offset[0], self.rect.y - self.rect_offset[1], *self.default_anim_sprite_size))

                    curr_frame_duration -= self.currentLevel.dt
                    self.default_anim_duration -= self.currentLevel.dt

                    yield
                
                curr_frame_duration = max_frame_duration
                frame_list_idx += 1

    def play_death_audio(self):
         if self.death_explosion_audio_name:
            free_audio_channel = pg.mixer.find_channel()
            if free_audio_channel:
                free_audio_channel.play(self.currentLevel.soundfx_collection[self.death_explosion_audio_name])
     
    def move_in_animation(self):
        if not self.move_in_on_spawn:
            return
        
        self.rect.x += self.move_in_offset
        constant_vel = False if not self.move_in_vel else True
        self.can_shoot = False

        if self.move_in_from == 1:

            while self.move_in_on_spawn and not self.move_in_anim_finished and self.rect.x > self.spawn_position[0]:
                if not constant_vel and (self.rect.x - self.spawn_position[0]) / 50 > 0.5:
                    self.move_in_vel = (self.rect.x - self.spawn_position[0]) / 50

                self.rect.x -= self.move_in_vel

                yield
        
        else:

            while self.move_in_on_spawn and not self.move_in_anim_finished and self.rect.x < self.spawn_position[0]:
                if not constant_vel and (self.spawn_position[0] - self.rect.x) / 50 > 0.5:
                    self.move_in_vel = (self.spawn_position[0] - self.rect.x) / 50

                self.rect.x += self.move_in_vel

                yield

        self.move_in_anim_finished = True
        self.can_shoot = True

        yield
    
    def draw_health_bar(self):

        health_bar: pg.Rect = pg.Rect(self.rect.x, self.rect.y - self.rect.height - 20, self.width, 5)

        while self.health > 0:
            health_bar.x = self.rect.x
            health_bar.y = self.rect.y - 25
 
            hls = colorsys.hls_to_rgb((health_bar.width / self.width * 100)/360, 0.5, 1)
            
            health_bar.width = self.health / self.max_health * self.width
           
            pg.draw.rect(self.currentLevel.parent.screen, list((i*255 for i in hls)), health_bar)

            yield
        yield



class Player(Ship):
    def __init__(self, currentLevel: Level, parent: Level, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        self.move_to_cursor_gen: Iterator[None] = None

        self.vel = kwargs.get("vel", 1)

        # iterators
        self.move_out_animation_gen: Iterator[None] = None
        self.move_in_animation_gen: Iterator[None] = None

        self.move_out_anim_finished: bool = True

        # multiplayer

        self.is_other_player: bool = False

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

    def handle_bullet_collision(self):
        i = 0 
        j = self.max_round_comparisons_per_frame

        while self.weapon.rounds: 
            i = min(i, len(self.weapon.rounds))
            j = min(j, len(self.weapon.rounds))
            for round in self.weapon.rounds[i:j]:
                for enemy in self.currentLevel.enemies + self.currentLevel.meteorites:
                    if enemy.is_alive and round.is_alive and round.rect.colliderect(enemy.rect):
                        enemy.take_health(self.weapon.damage)
                        round.is_alive = False
                        enemy.handle_health()

            i += self.max_round_comparisons_per_frame
            j += self.max_round_comparisons_per_frame

            if j > len(self.weapon.rounds):
                i = 0
                j = self.max_round_comparisons_per_frame
            
            yield
            
        yield
        
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

    def move_out_animation(self):
        self.immune = True
        self.move_out_anim_finished = False
        self.can_shoot = False

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
        self.can_shoot = True

        yield



class StandardEnemy(Ship):
    def __init__(self, currentLevel: Level, parent: Level, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        # ship sprite
        self.image_path = kwargs.get("image_path", "images/enemy/enemy_ship1.png")
        self.image = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_path), 270), (self.width, self.height))

        self.random_shoot_cooldowns: list[float] = kwargs.get("random_shoot_cooldowns", [1, 1.5, 2, 2.5, 3, 5])

        # bounce/wave movement
        self.bounce: bool = kwargs.get("bounce", True)
        self.bounce_speed: float = kwargs.get("bounce_speed", 2) # increment for curr_angle
        self.curr_angle: float = 0 # to get the y ratio
        self.bounce_height: int = kwargs.get("bounce_height", 10) # radius of circle
        self.bounce_delay: float = kwargs.get("bounce_delay", 0)

        # hit/damage indication
        self.image_hit_path = kwargs.get("image_hit_path", "images/enemy/enemy_ship1_hit1.png")
        self.image_hit = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_hit_path), 270), (self.width, self.height))
    
        # iterators
        self.move_in_animation_gen: Iterator[None] = None

    def shoot(self):
        self.weapon.shoot_cooldown = random.choice(self.random_shoot_cooldowns)
        while self.can_shoot:

            # removed dedicated shoot cooldown for enemies, improves performance
            
            if self.currentLevel.is_rect_onscreen(self.rect):
                self.weapon.max_shoot_cooldown = random.choice(self.random_shoot_cooldowns)
                
                if not self.weapon.shoot_gen:
                        self.weapon.shoot_gen = self.weapon.shoot()   
                try:
                    next(self.weapon.shoot_gen)
                except StopIteration:
                    self.weapon.shoot_gen = self.weapon.shoot()   
                
            yield
        yield

    def update_position(self):
        if self.move_in_on_spawn and not self.move_in_anim_finished: 
            if not self.move_in_animation_gen:
                self.move_in_animation_gen = self.move_in_animation()
            try:
                next(self.move_in_animation_gen)
            except StopIteration:
                self.move_in_animation_gen = self.move_in_animation()

        if self.bounce_delay > 0:
            self.bounce_delay -= self.currentLevel.dt

        if self.bounce and self.bounce_delay <= 0:
            # self.rect.x = self.spawn_position[0] + self.bounce_height * math.cos(self.curr_angle)
            self.rect.y = self.spawn_position[1] + self.bounce_height * math.sin(math.radians(self.curr_angle))
            
            self.curr_angle += self.bounce_speed

    def handle_health(self):
        if self.health <= 0:
            self.is_alive = False
        
        if self.death_anim_duration <= 0:
            self.rect = None

    def handle_bullet_collision(self):
        i = 0 
        j = self.max_round_comparisons_per_frame

        while self.weapon.rounds:
            i = min(i, len(self.weapon.rounds))
            j = min(j, len(self.weapon.rounds))

            for round in self.weapon.rounds:
                
                for enemy in [self.currentLevel.player] + self.currentLevel.meteorites:
                    if enemy.is_alive and round.is_alive and round.rect.colliderect(enemy.rect):
                        enemy.take_health(self.weapon.damage)
                        round.is_alive = False
                        enemy.handle_health()
            
            i += self.max_round_comparisons_per_frame
            j += self.max_round_comparisons_per_frame

            if j > len(self.weapon.rounds):
                i = 0
                j = self.max_round_comparisons_per_frame
            
            yield
        
        yield



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
    
    def activate(self):
        self.active = True
        self.rect = None



class PowerupWeapon(Powerup):
    def __init__(self, currentLevel: Level, parent: Level, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        self.weapon: Weapon = kwargs.get("weapon", Weapon1(currentLevel, parent=None))

    def handle_collision(self):
        if self.currentLevel.player.rect and self.rect.colliderect(self.currentLevel.player.rect):
            self.activate()
    
    def effect(self):
        self.currentLevel.player.weapon = self.weapon
        self.weapon.parent = self.currentLevel.player
        self.weapon.round_spawn_offset = [self.weapon.parent.rect.width, self.weapon.parent.rect.height//2]

        self.finished = True 



class PowerupHealth(Powerup):
    def __init__(self, currentLevel: Level, parent: Level, **kwargs):
        super().__init__(currentLevel, parent, **kwargs)

        self.health_value: float = kwargs.get("health_value", 50)

        self.image_path: str = kwargs.get("image_path", "images/Health & Ammo Pickups/health-green 32px.png")
        self.image = pg.transform.scale(pg.transform.rotate(pg.image.load(self.image_path), self.angle), (self.width, self.height))

    def handle_collision(self):
        if self.currentLevel.player.rect and self.rect.colliderect(self.currentLevel.player.rect):
            self.activate()
            
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
            self.activate()
    
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
            self.activate()
    
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
        self.rect.width = self.rect.height = random.randint(*self.currentLevel.meteorite_size_range)
        self.health = self.max_health = self.rect.width * 20

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
                
                # if meteor is fully off-screen
                if not self.currentLevel.is_rect_onscreen(self.rect, offset=max(self.rect.width, self.rect.height)):
                    self.reset()
                    
            self.rect.x += math.cos(math.radians(self.angle)) * self.vel
            self.rect.y += -math.sin(math.radians(self.angle)) * self.vel
    
    def handle_health(self):
        if self.health <= 0:
            self.is_alive = False
        
        if self.death_anim_duration <= 0:
            self.rect = None

    def draw(self):
        if self.draw_rect:
            pg.draw.rect(self.currentLevel.parent.screen, (255, 0, 0), self.rect, 2)

        self.currentLevel.parent.screen.blit(self.image, self.rect)

    def collide(self, player: Player):
        player.take_health(self.damage)
        self.is_alive = False

    def handle_collision(self):
        if self.currentLevel.player.rect and self.rect.colliderect(self.currentLevel.player.rect):
            self.collide(self.currentLevel.player)
    
        