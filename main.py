from AlienInvasion import Game, Level, Ship, Player, Weapon, Weapon1, Weapon2, Weapon3, Weapon4, Weapon5, StandardEnemy, PowerupWeapon, PowerupHealth, PowerupShield, PowerupDamageBoost, Meteorite
import random

def create_fleet(currentLevel: Level, num: int, left: int, top: int, spacing: int, **kwargs) -> list[StandardEnemy]:
    fleet = []

    for i in range(1, num+1):
        enemy: Ship = StandardEnemy(
            currentLevel, 
            parent=currentLevel, 
            spawn_position=[left, top + (spacing * i)], 
            death_sprite_collection_name="explosion1", 
            default_sprite_collection_name="enemy1_default_anim",
            default_anim_sprite_size=[100, 50],
            hit_indication_sprite_collection_name="enemy1_default_anim_hit",
            width=kwargs.get("width", 50),
            height=kwargs.get("height", 50),
            random_shoot_cooldowns=kwargs.get("random_shoot_cooldowns", [1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3]),
            angle=180,
            rect_offset=[10, 0],
            death_anim_duration=0.5,
            move_in_offset=kwargs.get("move_in_offset", 900),
            move_in_from=1,
            max_death_explosion_interval_time=0.15,
            num_death_explosions=3,
            bounce_speed=random.choice([2]),
            bounce_height=kwargs.get("bounce_height", random.choice([7, 8, 9, 10, 11])),
            # hit_indication_audio_name="hitmarker_2"
            draw_health=kwargs.get("draw_healt", False),
            bounce_delay=kwargs.get("bounce_delay", 0),
            draw_rect=False,
            
            
        )

        if kwargs.get("weapon"):
            enemy_weapon: Weapon = kwargs.get("weapon")(currentLevel, parent=enemy)
        else:
            enemy_weapon: Weapon = Weapon1(currentLevel, parent=enemy)

        enemy.weapon = enemy_weapon
        enemy_weapon.round_color = kwargs.get("round_color", (0, 150, 255))
        enemy_weapon.round_size = kwargs.get("round_size", (15, 5))
        enemy_weapon.max_shoot_cooldown = 1
        enemy_weapon.shoot_cooldown = 1
        enemy_weapon.round_death_sprite_collection_name="explosion1"
        enemy_weapon.shoot_angle = 180
        enemy_weapon.round_image_path = kwargs.get("round_image_path", "images/Pixel SHMUP Free 1.2/projectile_3.png")
        enemy_weapon.round_spawn_offset = [0, enemy.rect.height//2]
        enemy_weapon.round_draw_rect=kwargs.get("round_draw_rect", False)

        fleet.append(enemy)
        
    return fleet

        
powerup_icons = {
    PowerupDamageBoost: "images/Health & Ammo Pickups/ammo-rifle 32px.png",
    PowerupShield: "images/Health & Ammo Pickups/health-armor 32px.png",
}

game: Game = Game(powerup_icons=powerup_icons)



class Level1(Level):
    def __init__(self, parent: Game, **kwargs):
        super().__init__(parent, **kwargs)
        self.soundfx_collection = {
            "hitmarker_2": "sounds/click_1.wav",
            "big_explosion_1": "sounds/big_explosion_1.wav",
        }
        self.sprite_collections = {
            "explosion1": 
            [
                "images/explosions/explosion1/explosion001.png",
                "images/explosions/explosion1/explosion002.png",
                "images/explosions/explosion1/explosion003.png",
                "images/explosions/explosion1/explosion004.png",
                "images/explosions/explosion1/explosion005.png",
                "images/explosions/explosion1/explosion006.png",
                "images/explosions/explosion1/explosion007.png",
                "images/explosions/explosion1/explosion008.png",
            ],
            
            "player_default_anim": 
            [
                "images/player/player_ship1.png",
                "images/player/player_ship2.png",
                "images/player/player_ship3.png",
                "images/player/player_ship4.png",
                "images/player/player_ship5.png",
                "images/player/player_ship6.png",
            ],
            "player_default_anim_hit": 
            [
                "images/player/player_ship_hit1.png",
                "images/player/player_ship_hit2.png",
                "images/player/player_ship_hit3.png",
                "images/player/player_ship_hit4.png",
                "images/player/player_ship_hit5.png",
                "images/player/player_ship_hit6.png",
                
            ],
            "enemy1_default_anim": 
            [
                "images/enemy/enemy_ship2_1.png",
                "images/enemy/enemy_ship2_2.png",
                "images/enemy/enemy_ship2_3.png",
                "images/enemy/enemy_ship2_4.png",
                "images/enemy/enemy_ship2_5.png",
                "images/enemy/enemy_ship2_6.png",
            ],
            "enemy1_default_anim_hit": 
            [
                "images/enemy/enemy_ship2_hit1.png",
                "images/enemy/enemy_ship2_hit2.png",
                "images/enemy/enemy_ship2_hit3.png",
                "images/enemy/enemy_ship2_hit4.png",
                "images/enemy/enemy_ship2_hit5.png",
                "images/enemy/enemy_ship2_hit6.png",
            ],
        }
        

        
        self.meteorite_spawn_x_position_range=[700, 1000]
        #self.meteorite_angle_range=[180, 270]
        self.meteorite_health_range=[200, 400]
        self.meteorite_vel_range=[1, 5]
        self.meteorite_size_range=[30, 150]
        self.meteorite_damage_range=[20, 100]
        self.meteorite_cooldown_range=[1, 5]

        # player
        self.player: Ship = Player(
            self, 
            parent=self,
            vel=10, 
            angle=0,
            width=75,
            death_sprite_collection_name="explosion1",
            default_sprite_collection_name="player_default_anim",
            hit_indication_sprite_collection_name="player_default_anim_hit",
            spawn_position=[150, (self.parent.screen_h//2)-50],
            max_health=300, 
            move_in_from=0,
            move_in_offset=-2500,
            rect_offset=[50, 0],
            draw_rect=True,
            
        )
        weapon1: Weapon = Weapon4(
            self, 
            parent=self.player, 
            max_shoot_cooldown=0.2, 
            round_death_sprite_collection_name="explosion1", 
            damage=15,
            round_size=[50, 7],
            round_angle=90,
            round_spawn_offset=[self.player.rect.width, self.player.rect.height//2],
            round_draw_rect=False,
           
            # round_vel=1
        )
    
        self.player.weapon = weapon1
        
        big_enemy = StandardEnemy(
            self, 
            parent=self, 
            width=110, 
            height=150, 
            default_anim_sprite_size=[280, 150],
            angle=180,
            spawn_position=[1000, 250], 
            death_sprite_collection_name="explosion1",
            default_sprite_collection_name="enemy1_default_anim",
            hit_indication_sprite_collection_name="enemy1_default_anim_hit",
            random_shoot_cooldowns=[0], 
            max_health=2000,
            move_in_from=1,
            num_death_explosions=10,
            death_explosion_audio_name="big_explosion_1",
            draw_health=True,
            draw_rect=False,
            rect_offset=[20, 0],
            # hit_indication_audio_name="hitmarker_2"
        )

        big_enemy_weapon = Weapon5(
            self, 
            parent=big_enemy, 
            round_death_sprite_collection_name="explosion1", 
            round_image_path="images/fireball.png",
            max_shoot_cooldown=1, 
            shoot_cooldown=0, 
            round_vel=10, 
            # rotation_speed=10, 
            damage=5, 
            shoot_angle=180,
            round_size=[20, 20],  
            num_rounds=20,
            round_spawn_offset=[0, big_enemy.rect.height//2]                       
        )

        big_enemy.weapon = big_enemy_weapon
        
        self.enemy_queue = [
            # create_fleet(self, 7, 1250, -75, 100, round_size=[25, 7], move_in_offset=2500) + create_fleet(self, 7, 1100, -75, 100, round_size=[25, 7], move_in_offset=1800) + create_fleet(self, 7, 950, -75, 100, round_size=[25, 7], move_in_offset=1500) + create_fleet(self, 7, 800, -75, 100, round_size=[25, 7], move_in_offset=1200), 
            # create_fleet(self, 7, 1250, -75, 100, round_size=[25, 7]) + create_fleet(self, 7, 1100, -75, 100, round_size=[25, 7]), 
            create_fleet(self, 7, 1250, -75, 100, round_size=[25, 7]) + [big_enemy], 
                            ]

        self.powerup_cooldown_range = [5, 30]
        self.powerup_spawn_range = [300, 1000]

        self.powerup_queue = [
            # PowerupWeapon(self, parent=self, cooldown=2, weapon=Weapon2(self, parent=None, round_sprite_collection_name="explosion1", damage=20), spawn_position=[500, -50], width=50, height=50),
            PowerupDamageBoost(self, parent=self, cooldown=random.randint(*self.powerup_cooldown_range), spawn_position=[random.randint(*self.powerup_spawn_range), -50], duration=10, width=75, height=75),
            PowerupHealth(self, parent=self, cooldown=random.randint(*self.powerup_cooldown_range), spawn_position=[random.randint(*self.powerup_spawn_range), -50], duration=10, width=75, height=75),
            PowerupDamageBoost(self, parent=self, cooldown=random.randint(*self.powerup_cooldown_range), spawn_position=[random.randint(*self.powerup_spawn_range), -50], duration=10, new_damage_value=50, width=75, height=75),
            PowerupShield(self, parent=self, cooldown=1, spawn_position=[random.randint(*self.powerup_spawn_range), -50], duration=10, width=75, height=75),
            PowerupShield(self, parent=self, cooldown=10, spawn_position=[random.randint(*self.powerup_spawn_range), -50], duration=10, width=75, height=75),
        ]

        self.meteorites = [
            Meteorite(self, parent=self, death_sprite_collection_name="explosion1", draw_rect=False),
            Meteorite(self, parent=self, death_sprite_collection_name="explosion1", draw_rect=False),
            Meteorite(self, parent=self, death_sprite_collection_name="explosion1", draw_rect=False),
        ]




class Level2(Level1):
    def __init__(self, parent: Game, **kwargs):
        super().__init__(parent, **kwargs)
        
        big_enemy = StandardEnemy(
            self, 
            parent=self, 
            width=150, 
            height=150, 
            spawn_position=[1000, 250], 
            death_sprite_collection_name="explosion1",
            default_sprite_collection_name="enemy1_default_anim",
            hit_indication_sprite_collection_name="enemy1_default_anim_hit",
            random_shoot_cooldowns=[0], 
            max_health=2000,
            move_in_from=1,
            num_death_explosions=10,
            death_explosion_audio_name="big_explosion_1",
            draw_health=True,
            # hit_indication_audio_name="hitmarker_2"
        )

        big_enemy = StandardEnemy(
            self, 
            parent=self, 
            width=110, 
            height=150, 
            default_anim_sprite_size=[210, 150],
            angle=180,
            spawn_position=[1000, 250], 
            death_sprite_collection_name="explosion1",
            default_sprite_collection_name="enemy1_default_anim",
            hit_indication_sprite_collection_name="enemy1_default_anim_hit",
            random_shoot_cooldowns=[0], 
            max_health=2000,
            move_in_from=1,
            num_death_explosions=10,
            death_explosion_audio_name="big_explosion_1",
            draw_health=True,
            draw_rect=False,
            rect_offset=[20, 0],
            # hit_indication_audio_name="hitmarker_2"
        )

        big_enemy_weapon = Weapon5(
            self, 
            parent=big_enemy, 
            round_death_sprite_collection_name="explosion1", 
            round_image_path="images/fireball.png",
            max_shoot_cooldown=1, 
            shoot_cooldown=0, 
            round_vel=10, 
            # rotation_speed=10, 
            damage=5, 
            shoot_angle=180,
            round_size=[20, 20],  
            num_rounds=20,
            round_spawn_offset=[0, big_enemy.rect.height//2]                       
        )

        big_enemy.weapon = big_enemy_weapon
        
        self.enemy_queue = [
            # create_fleet(self, 7, 1250, -75, 100, round_size=[25, 7], move_in_offset=2500) + create_fleet(self, 7, 1100, -75, 100, round_size=[25, 7], move_in_offset=1800) + create_fleet(self, 7, 950, -75, 100, round_size=[25, 7], move_in_offset=1500) + create_fleet(self, 7, 800, -75, 100, round_size=[25, 7], move_in_offset=1200), 
            # create_fleet(self, 7, 1250, -75, 100, round_size=[25, 7]) + create_fleet(self, 7, 1100, -75, 100, round_size=[25, 7]), 
            create_fleet(self, 4, 1250, -150, 200, round_size=[25, 7], bounce_height=20, bounce_delay=2) + create_fleet(self, 3, 1100, 0, 200, weapon=Weapon4, round_size=[25, 25], bounce_height=20, random_shoot_cooldowns=[0.25, 0.3, 0.4, 0.5, 0.6, 0.7], round_image_path="images/fireball.png") + create_fleet(self, 4, 950, -150, 200, round_size=[25, 7], bounce_height=20, bounce_delay=1), 
                            ]

        


game.levels = [Level1, Level2]

game.start()