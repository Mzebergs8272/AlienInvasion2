from AlienInvasion import Game, Level, Ship, Player, Weapon, Weapon1, Weapon2, Weapon3, Weapon4, StandardEnemy, PowerupWeapon, PowerupHealth, PowerupShield, PowerupDamageBoost, Meteorite
import random, copy

def instantiate_fleet(currentLevel: Level, num: int, left: int, top: int, spacing: int, **kwargs) -> list[StandardEnemy]:
    fleet = []

    for i in range(1, num+1):
        enemy: Ship = StandardEnemy(
            currentLevel, 
            parent=currentLevel, 
            spawn_position=[left, top + (spacing * i)], 
            sprite_collection_name="explosion1", 
            width=kwargs.get("width", 100),
            height=kwargs.get("height", 75),
            random_shoot_cooldowns=kwargs.get("random_shoot_cooldowns", [1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3]),
            move_in_vel=10,
            angle=0,
    
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
        enemy_weapon.round_sprite_collection_name="explosion1"
        enemy_weapon.shoot_angle = 180

        fleet.append(enemy)
        
    return fleet

powerup_icons = {
    PowerupDamageBoost: "images/Health & Ammo Pickups/ammo-rifle 32px.png",
    PowerupShield: "images/Health & Ammo Pickups/health-armor 32px.png",
   
}

game: Game = Game(powerup_icons=powerup_icons)

sprite_collections = {
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




level1: Level = Level(
    parent=game, 
    sprite_collections=sprite_collections,
    meteorite_spawn_x_position_range=[700, 1000],
    # meteorite_angle_range=[180, 270],
    meteorite_health_range=[200, 400],
    meteorite_vel_range=[1, 5],
    meteorite_size_range=[30, 150],
    meteorite_damage_range=[20, 100],
    meteorite_cooldown_range=[1, 5],
)

# player
player: Ship = Player(
    level1, 
    parent=level1,
    vel=10, 
    sprite_collection_name="explosion1",
    spawn_position=[150, game.screen_h//2],
    max_health=300
)
weapon1: Weapon = Weapon1(
    level1, 
    parent=player, 
    max_shoot_cooldown=0.2, 
    round_sprite_collection_name="explosion1", 
    damage=20

)

player.weapon = weapon1
level1.player = player

big_enemy = StandardEnemy(
    level1, 
    parent=level1, 
    width=150, 
    height=150, 
    spawn_position=[1100, 250], 
    sprite_collection_name="explosion1",
    random_shoot_cooldowns=[1], 
    max_health=2000,
    num_death_explosions=10
)

big_enemy_weapon = Weapon4(
    level1, 
    parent=big_enemy, 
    round_sprite_collection_name="explosion1", 
    max_shoot_cooldown=0, 
    shoot_cooldown=0, 
    round_vel=3, 
    rotation_speed=10, 
    damage=5, 
    shoot_angle=180, 
    round_size=[12, 12],
    
)

big_enemy.weapon = big_enemy_weapon

level1.enemy_queue = [
    instantiate_fleet(level1, 7, 1250, -75, 100) + instantiate_fleet(level1, 7, 1100, -75, 100), 
    instantiate_fleet(level1, 7, 1250, -75, 100) + [big_enemy], 
                      ]

powerup_cooldown_range = [5, 30]
powerup_spawn_range = [300, 1000]

powerup1 = PowerupWeapon(level1, parent=level1, weapon=Weapon2(level1, parent=None, round_sprite_collection_name="explosion1", damage=20), spawn_position=[500, -50], width=50, height=50)
powerup2 = PowerupDamageBoost(level1, parent=level1, cooldown=random.randint(*powerup_cooldown_range), spawn_position=[random.randint(*powerup_spawn_range), -50], duration=10, width=75, height=75)
powerup3 = PowerupHealth(level1, parent=level1, cooldown=random.randint(*powerup_cooldown_range), spawn_position=[random.randint(*powerup_spawn_range), -50], duration=10, width=75, height=75)
powerup4 = PowerupDamageBoost(level1, parent=level1, cooldown=random.randint(*powerup_cooldown_range), spawn_position=[random.randint(*powerup_spawn_range), -50], duration=10, new_damage_value=50, width=75, height=75)
powerup5 = PowerupShield(level1, parent=level1, cooldown=1, spawn_position=[random.randint(*powerup_spawn_range), -50], duration=10, width=75, height=75)
powerup6 = PowerupShield(level1, parent=level1, cooldown=10, spawn_position=[random.randint(*powerup_spawn_range), -50], duration=10, width=75, height=75)


level1.powerup_queue = [
    powerup1, 
    powerup2,
    powerup3,
    powerup4,
    powerup5,
    powerup6
]

meteorite1 = Meteorite(level1, parent=level1, sprite_collection_name="explosion1")
meteorite2 = Meteorite(level1, parent=level1, sprite_collection_name="explosion1")
meteorite3 = Meteorite(level1, parent=level1, sprite_collection_name="explosion1")
level1.meteorites = [
    meteorite1,
    meteorite2,
    meteorite3
]



game.levels = [level1]
game.start()