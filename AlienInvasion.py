import pygame as pg, sys, math, os, random
from abc import abstractmethod, ABCMeta

# TODO: create bullet animations


class Game:
    def __init__(self):
        self.running: bool = True
        self.levels: list[Level] = []
        
        self.screen_w = 1200
        self.screen_h = 600
        self.screen = pg.display.set_mode((self.screen_w, self.screen_h))

        self.clock = pg.time.Clock()

        pg.display.set_caption("Alien Invasion 2")

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
                self.clock.tick(60)
    

                
class Level:
    def __init__(self, parent: Game):
        self.parent: Game = parent
        self.running: bool = True

        self.player: Player = None
        self.enemy_queue: list[list[StandardEnemy]] = []
        self.enemies: list[StandardEnemy] = []

        self.clock = pg.time.Clock()
        self.dt = 0

        # any new sprite lists are defined here, filled in main.py, and accessed anywhere in this file
        self.sprite_collections: dict[str: list[pg.Surface]] = {"explosion1": [],
                                                                "explosion2": []
                                                                }

        # pg.mouse.set_visible(False)
        
    
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
        if 0 < rect.x < self.parent.screen_w - rect.width and 0 < rect.y < self.parent.screen_h - rect.height:
            return True
        return False
    
    def handle_enemies(self) -> None:
        if not self.enemies and self.enemy_queue:
            self.enemies = self.enemy_queue.pop()
            print(len(self.enemies))

    def start(self) -> None:

        self.load_sprites()

        while self.running:
            self.keys = pg.key.get_pressed()
            self.check_events()
            self.parent.screen.fill("black")

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

                if 0 < pg.mouse.get_pos()[0] < self.parent.screen_w and \
                    0 < pg.mouse.get_pos()[1] < self.parent.screen_h:
                    self.player.rect.x, self.player.rect.y = pg.mouse.get_pos()[0] - self.player.rect.width//2, pg.mouse.get_pos()[1] - self.player.rect.height//2
                    
                if self.keys[pg.K_SPACE] or pg.mouse.get_pressed()[0]:
                    self.player.shoot(0)

                next(self.player.weapon.update_rounds())
                self.player.handle_bullet_collision() 
            else:
                next(self.player.death_animation())
            
            for enemy in self.enemies:
                if enemy.is_alive:
                    next(enemy.shoot(180))
                    next(enemy.weapon.update_rounds())
                    enemy.handle_bullet_collision()
                else:
                    next(enemy.death_animation())
                
            pg.display.update()
            self.dt = self.clock.tick(60) / 1000


# for weapons
class Round:
    def __init__(self, game: Game, parent: object, angle: float, location: list[int, int]):
        self.parent: Weapon = parent
        self.game: Game = game

        self.angle: float = angle
        self.width: int = 7
        self.height: int = 5
        self.vel: int = 10
        self.color: tuple[int] = (255, 0, 0)

        self.location: list[int] = location or [self.parent.parent.rect.x + self.parent.parent.rect.width, self.parent.parent.rect.y + self.parent.parent.rect.height//2]
        self.rect: pg.Rect = pg.Rect(self.location[0], self.location[1], self.width, self.height)

        self.is_alive = True

        # death animation
        self.sprite_list: list[pg.Surface] = self.parent.parent.parent.sprite_collections["explosion1"]
        self.death_anim_duration = 0.2
        self.max_sprite_frame_duration = self.death_anim_duration / len(self.sprite_list)
        self.sprite_frame_duration = self.max_sprite_frame_duration
        self.sprite_frame_index = 0
        self.sprite_size: list[int, int] = [35, 35]

    def draw(self):
        pg.draw.rect(self.game.screen, self.color, self.rect)
    
    def death_animation(self):
        if not isinstance(self.sprite_list[0], pg.Surface): 
            self.sprite_list = self.parent.parent.parent.sprite_collections["explosion1"]
        while not self.is_alive and self.rect and self.death_anim_duration > 0:
            while self.sprite_frame_duration > 0:
                self.game.screen.blit(
                    pg.transform.scale(
                        self.sprite_list[self.sprite_frame_index], 
                        self.sprite_size
                    ), 
                    (
                        self.rect.x - self.sprite_size[0]//2, 
                        self.rect.y - self.sprite_size[1]//2
                    )
                )

                self.death_anim_duration -= self.parent.parent.parent.dt
                self.sprite_frame_duration -= self.parent.parent.parent.dt
                yield

            self.sprite_frame_index += 1
            self.sprite_frame_duration = self.max_sprite_frame_duration
            
        self.rect = None

        yield



class Weapon(metaclass=ABCMeta):
    def __init__(self, game: Game, parent: object=None):
        self.parent: Player = parent
        self.game = game

        self.rounds: list[Round] = []
        self.damage: float = 10

    @abstractmethod
    def shoot(self):
        pass

    # draws and updates round positions
    @abstractmethod
    def update_rounds(self):
        pass



class Weapon1(Weapon):
    def __init__(self, game: Game, max_shoot_cooldown: float, parent=None):
        super().__init__(game, parent)

        self.max_shoot_cooldown: float = max_shoot_cooldown
        self.shoot_cooldown: float = self.max_shoot_cooldown

        self.round_color: tuple = (255, 0, 0)

        self.round_size: tuple[int, int] = (7, 5)
    
    def shoot(self, angle: int, position: list[int, int]=[]):
        if self.shoot_cooldown > 0: self.shoot_cooldown -= self.parent.parent.dt
        if self.shoot_cooldown <= 0:
            round = Round(self.game, self, angle, position)
            round.width = self.round_size[0]
            round.height = self.round_size[1]
            round.color = self.round_color
            self.rounds.append(round)
            self.shoot_cooldown = self.max_shoot_cooldown

    def update_rounds(self):
        
        while self.rounds:
            self.rounds = [r for r in self.rounds if r.rect is not None]
            
            for round in self.rounds:
                if round.is_alive and self.parent.parent.is_rect_onscreen(round.rect):
                    round.draw()
                
                    upwards = math.sin(math.radians(round.angle))
                    right = math.cos(math.radians(round.angle))

                    round.rect.x += right * round.vel
                    round.rect.y += upwards * round.vel
                else:
                    round.is_alive = False
                    next(round.death_animation())

                
            yield

        yield



class Ship(metaclass=ABCMeta):
    def __init__(self, parent: Level):
        self.parent: Level = parent
        self.game: Game = self.parent.parent
        self.weapon: Weapon = None

        #health
        self.max_health: float = 100
        self.health: float = self.max_health

        # hit indication
        self.max_hit_indication_duration: float = 0.1
        self.hit_indication_duration: float = 0
        self.image_hit: pg.Surface = None

        # death animation
        self.death_anim_duration: float = 0.5
        self.is_alive: bool = True

        # ship sprite
        self.image: pg.Surface = None
        self.rect: pg.Rect = None

    @abstractmethod
    def shoot(self, angle: int) -> None:
        pass

    def draw(self) -> None:
        self.game.screen.blit(self.image, self.rect)

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
            self.game.screen.blit(self.image_hit, self.rect)
            self.hit_indication_duration -= self.parent.dt
            yield

        yield
        


class Player(Ship):
    def __init__(self, parent: Level, position: list[int, int] = [50,50]):
        super().__init__(parent)
        self.width: int = 100
        self.height: int = 75
        self.position: list[int, int] = position

        self.vel: int = 10

        # ship sprite
        self.image = pg.transform.scale(pg.transform.rotate(pg.image.load("images/player/player_ship.png"), 270), (self.width, self.height))
        self.rect = self.image.get_rect(top=position[0], left=position[1])

        # hit/damage indication
        self.image_hit = pg.transform.scale(pg.transform.rotate(pg.image.load("images/player/player_ship_hit1.png"), 270), (self.width, self.height))
        
        # death animation
        self.sprite_list: list[pg.Surface] = self.parent.sprite_collections["explosion2"]
        self.death_anim_duration = 0.5
        self.max_sprite_frame_duration = self.death_anim_duration / len(self.sprite_list)
        self.sprite_frame_duration = self.max_sprite_frame_duration
        self.sprite_frame_index = 0
        self.sprite_size: list[int, int] = [100, 100]
        

    def shoot(self, angle: int) -> None:
        self.weapon.shoot(angle)
    
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

    def death_animation(self):
        if not isinstance(self.sprite_list[0], pg.Surface): self.sprite_list = self.parent.sprite_collections["explosion2"]
        while not self.is_alive and self.rect and self.death_anim_duration > 0:
            while self.sprite_frame_duration > 0:
                self.game.screen.blit(
                    pg.transform.scale(
                        self.sprite_list[self.sprite_frame_index], 
                        self.sprite_size
                    ), 
                    (
                        self.rect.x + self.sprite_size[0]//2 + random.choice([x for x in range(-75, 75)]), 
                        self.rect.y + self.sprite_size[1]//2 + random.choice([y for y in range(-50, 50)])
                    )
                )

                self.death_anim_duration -= self.parent.dt
                self.sprite_frame_duration -= self.parent.dt
                yield

            self.sprite_frame_index += 1
            self.sprite_frame_duration = self.max_sprite_frame_duration

        yield     
        
          
                           

class StandardEnemy(Ship):
    def __init__(self, parent: Level, position: list[int, int] = [100, 100]):
        super().__init__(parent)

        self.width = 100
        self.height = 75
        self.position = position

        self.random_shoot_cooldowns: list[float] = []
        self.shoot_cooldown: float = None

        # bounce/wave movement
        self.bounce: bool = True
        self.bounce_speed: float = 2 # increment for curr_angle
        self.curr_angle: float = 0 # to get the y ratio
        self.bounce_height: int = 10 # radius of circle

        # death animation
        self.sprite_list: list[pg.Surface] = self.parent.sprite_collections["explosion2"]
        self.death_anim_duration = 0.5
        self.max_sprite_frame_duration = self.death_anim_duration / len(self.sprite_list)
        self.sprite_frame_duration = self.max_sprite_frame_duration
        self.sprite_frame_index = 0
        self.sprite_size: list[int, int] = [100, 100]
        self.is_alive = True

        # animation on spawn
        self.move_in_on_spawn: bool = True
        self.initial_position: list[int, int] = [self.position[0] + 300, self.position[1]]
        self.move_in_vel: float = 3

        # ship image
        self.image = pg.transform.scale(pg.transform.rotate(pg.image.load("images/enemy/enemy_ship1.png"), 270), (self.width, self.height))
        self.rect: pg.Rect = self.image.get_rect(left=position[0], top=position[1])

        # hit/damage indication
        self.image_hit = pg.transform.scale(pg.transform.rotate(pg.image.load("images/enemy/enemy_ship1_hit2.png"), 270), (self.width, self.height))
        self.max_hit_indication_duration = 0.1
        self.hit_indication_duration = 0

    def shoot(self, angle: int):
        while True:
            if self.shoot_cooldown is None:
                if self.random_shoot_cooldowns:
                    self.shoot_cooldown = random.choice(self.random_shoot_cooldowns)
                else:
                    self.shoot_cooldown = 1
        
            self.shoot_cooldown -= self.parent.dt

            if self.shoot_cooldown <= 0 and self.parent.is_rect_onscreen(self.rect):
                self.weapon.shoot(angle, [self.rect.x, self.rect.y + self.rect.height//2])
                self.shoot_cooldown = random.choice(self.random_shoot_cooldowns)

            yield

    def move_in_anim(self):
        if self.rect.x == self.position[0]:
            self.rect.x += 300
        while self.rect.x > self.position[0]:
            self.rect.x -= self.move_in_vel
          
            if self.rect.x > self.position[0]:
                yield

        self.move_in_on_spawn = False

        yield

    def update_position(self):
        if self.move_in_on_spawn: next(self.move_in_anim())
            
        if self.bounce:
            # self.rect.x = center[0] + radius * math.cos(angle)
            self.rect.y = self.position[1] + self.bounce_height * math.sin(math.radians(self.curr_angle))
            
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
    
    def death_animation(self):
        if not isinstance(self.sprite_list[0], pg.Surface): self.sprite_list = self.parent.sprite_collections["explosion2"]
        while not self.is_alive and self.rect and self.death_anim_duration > 0:
            while self.sprite_frame_duration > 0:
                self.game.screen.blit(
                    pg.transform.scale(self.sprite_list[self.sprite_frame_index], self.sprite_size), (self.rect.x, self.rect.y))

                self.death_anim_duration -= self.parent.dt
                self.sprite_frame_duration -= self.parent.dt
                yield

            self.sprite_frame_index += 1
            self.sprite_frame_duration = self.max_sprite_frame_duration

        self.rect = None

        yield  





