from AlienInvasion import Game, Level, Ship, Player, Weapon, Weapon1, Weapon2, Weapon3, Weapon4, StandardEnemy


def instantiate_fleet(currentLevel: Level, num: int, left: int, top: int, spacing: int, **kwargs) -> list[StandardEnemy]:
    fleet = []

    for i in range(1, num+1):
        enemy: Ship = StandardEnemy(
            currentLevel, 
            parent=currentLevel, 
            spawn_position=[left, top + (spacing * i)], 
            sprite_collection_name="explosion2", 
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

game: Game = Game()

sprite_collections = {
    "explosion1": 
    [
        "images/explosions/explosion1_1.png",
        "images/explosions/explosion1_2.png",
        "images/explosions/explosion1_3.png",
        "images/explosions/explosion1_4.png"
    ],
    "explosion2": 
    [
        "images/explosions/explosion2_1.png",
        "images/explosions/explosion2_2.png",
        "images/explosions/explosion2_3.png",
        "images/explosions/explosion2_4.png"
    ]
}

level1: Level = Level(parent=game, sprite_collections=sprite_collections)

# player
player: Ship = Player(
    level1, 
    parent=level1,
    vel=10, 
    sprite_collection_name="explosion2",
    spawn_position=[150, game.screen_h//2],
    max_health=10000
)
weapon1: Weapon = Weapon4(
    level1, 
    parent=player, 
    max_shoot_cooldown=0.2, 
    round_sprite_collection_name="explosion1", 

)

player.weapon = weapon1
level1.player = player

big_enemy = StandardEnemy(level1, parent=level1, width=150, height=150, spawn_position=[1100, 250], sprite_collection_name="explosion2", random_shoot_cooldowns=[0.2], max_health=2000)
big_enemy_weapon = Weapon4(level1, parent=big_enemy, round_sprite_collection_name="explosion1", max_shoot_cooldown=0, shoot_cooldown=0, round_vel=5, rotation_speed=10, damage=0.5, shoot_angle=180)
big_enemy.weapon = big_enemy_weapon



level1.enemy_queue = [instantiate_fleet(level1, 7, 1250, -75, 100), 
                      instantiate_fleet(level1, 7, 1250, -75, 100) + [big_enemy], 
                      ]


game.levels = [level1]
game.start()