from AlienInvasion import Game, Level, Ship, Player, Weapon, Weapon1, Weapon2, Weapon3, Weapon4, StandardEnemy, PowerupWeapon, PowerupHealth, PowerupShield, PowerupDamageBoost, Meteorite
import random, copy

def create_fleet(currentLevel: Level, num: int, left: int, top: int, spacing: int, **kwargs) -> list[StandardEnemy]:
    fleet = []

    for i in range(1, num+1):
        enemy: Ship = StandardEnemy(
            currentLevel, 
            parent=currentLevel, 
            spawn_position=[left, top + (spacing * i)], 
            death_sprite_collection_name="explosion1", 
            width=kwargs.get("width", 100),
            height=kwargs.get("height", 75),
            random_shoot_cooldowns=kwargs.get("random_shoot_cooldowns", [1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3]),
            move_in_vel=10,
            angle=0,
            death_anim_duration=0.5,
            max_death_explosion_interval_time=0.15,
            num_death_explosions=3
        )

        if kwargs.get("weapon"):
            enemy_weapon: Weapon = kwargs.get("weapon")(currentLevel, parent=enemy)
        else:
            enemy_weapon: Weapon = Weapon1(currentLevel, parent=enemy)

        enemy.weapon = enemy_weapon
        enemy_weapon.round_color = kwargs.get("round_color", (0, 150, 255))
        enemy_weapon.round_size = kwargs.get("round_size", (15, 5))
        enemy_weapon.max_shoot_cooldown = 0
        enemy_weapon.shoot_cooldown = 0
        enemy_weapon.round_death_sprite_collection_name="explosion1"
        enemy_weapon.shoot_angle = 180
        enemy_weapon.round_image_path = "images\Pixel SHMUP Free 1.2\projectile_3.png"

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
            "hitmarker_2": "sounds/hitmarker_3.wav"
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
            "explosion2": 
            [
                "images/explosions/explosion2/explosion001.png",
                "images/explosions/explosion2/explosion002.png",
                "images/explosions/explosion2/explosion003.png",
                "images/explosions/explosion2/explosion004.png"
            ],
            "explosion3":
            [
                "images/explosions/explosion3/explosion001.png",
                "images/explosions/explosion3/explosion002.png",
                "images/explosions/explosion3/explosion003.png",
                "images/explosions/explosion3/explosion004.png"
            ]
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
            death_sprite_collection_name="explosion1",
            spawn_position=[150, self.parent.screen_h//2],
            max_health=300, 
        )
        weapon1: Weapon = Weapon1(
            self, 
            parent=self.player, 
            max_shoot_cooldown=0.2, 
            round_death_sprite_collection_name="explosion1", 
            damage=100,
            round_size=[25, 7],
            round_angle=90
        )
    
        self.player.weapon = weapon1
        
        big_enemy = StandardEnemy(
            self, 
            parent=self, 
            width=150, 
            height=150, 
            spawn_position=[1100, 250], 
            death_sprite_collection_name="explosion1",
            random_shoot_cooldowns=[1], 
            max_health=2000,
            num_death_explosions=10
        )

        big_enemy_weapon = Weapon4(
            self, 
            parent=big_enemy, 
            round_death_sprite_collection_name="explosion1", 
            max_shoot_cooldown=0, 
            shoot_cooldown=0, 
            round_vel=7, 
            rotation_speed=10, 
            damage=5, 
            round_size=[20, 20],
            
                       
        )

        big_enemy.weapon = big_enemy_weapon
        
        # occassional freezing is linked to big_enemy, maybe
        self.enemy_queue = [
            create_fleet(self, 7, 1250, -75, 100) + create_fleet(self, 7, 1100, -75, 100) + create_fleet(self, 7, 950, -75, 100) + create_fleet(self, 7, 800, -75, 100), 
            create_fleet(self, 7, 1250, -75, 100) + create_fleet(self, 7, 1100, -75, 100), 
            create_fleet(self, 7, 1250, -75, 100, round_size=[25, 7]) + [big_enemy], 
                            ]

        self.powerup_cooldown_range = [5, 30]
        self.powerup_spawn_range = [300, 1000]

        powerup1 = PowerupWeapon(self, parent=self, cooldown=2, weapon=Weapon2(self, parent=None, round_sprite_collection_name="explosion1", damage=20), spawn_position=[500, -50], width=50, height=50)
        powerup2 = PowerupDamageBoost(self, parent=self, cooldown=random.randint(*self.powerup_cooldown_range), spawn_position=[random.randint(*self.powerup_spawn_range), -50], duration=10, width=75, height=75)
        powerup3 = PowerupHealth(self, parent=self, cooldown=random.randint(*self.powerup_cooldown_range), spawn_position=[random.randint(*self.powerup_spawn_range), -50], duration=10, width=75, height=75)
        powerup4 = PowerupDamageBoost(self, parent=self, cooldown=random.randint(*self.powerup_cooldown_range), spawn_position=[random.randint(*self.powerup_spawn_range), -50], duration=10, new_damage_value=50, width=75, height=75)
        powerup5 = PowerupShield(self, parent=self, cooldown=1, spawn_position=[random.randint(*self.powerup_spawn_range), -50], duration=10, width=75, height=75)
        powerup6 = PowerupShield(self, parent=self, cooldown=10, spawn_position=[random.randint(*self.powerup_spawn_range), -50], duration=10, width=75, height=75)

        self.powerup_queue = [
            # powerup1, 
            powerup2,
            powerup3,
            powerup4,
            powerup5,
            powerup6
        ]

        meteorite1 = Meteorite(self, parent=self, death_sprite_collection_name="explosion1")
        meteorite2 = Meteorite(self, parent=self, death_sprite_collection_name="explosion1")
        meteorite3 = Meteorite(self, parent=self, death_sprite_collection_name="explosion1")
        self.meteorites = [
            meteorite1,
            meteorite2,
            meteorite3
        ]


class Level2(Level1):
    def __init__(self, parent):
        super().__init__(parent)




game.levels = [Level1, Level1]

game.start()