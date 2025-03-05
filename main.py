from AlienInvasion import Game, Level, Ship, Player, Weapon, Weapon1, StandardEnemy



game = Game()
level1 = Level(parent=game)


def instantiate_fleet(num: int, left: int, top: int, spacing: int, **kwargs) -> list[StandardEnemy]:
    fleet = []

    for i in range(1, num+1):

        enemy: Ship = StandardEnemy(level1, [left, top + (spacing * i)])
        enemy.rect.width = kwargs.get("width", enemy.width)
        enemy.rect.height = kwargs.get("height", enemy.height)

        if kwargs.get("weapon"):
            enemy_weapon = kwargs.get("weapon")(game=game, max_shoot_cooldown=0, parent=enemy)
        else:
            enemy_weapon = Weapon1(game=game, max_shoot_cooldown=0, parent=enemy)

        # enemy_weapon: Weapon = kwargs.get("weapon", )
        enemy.weapon = enemy_weapon
        enemy.random_shoot_cooldowns = kwargs.get("random_shoot_cooldowns", [1, 1,5, 2, 2.5, 3])
        enemy_weapon.round_color = kwargs.get("round_color", (0, 150, 255))
        enemy_weapon.round_size = kwargs.get("round_size", (7, 5))

        fleet.append(enemy)
        
    return fleet


level1.sprite_collections["explosion1"] = [
    "images/explosions/explosion1_1.png",
    "images/explosions/explosion1_2.png",
    "images/explosions/explosion1_3.png",
    "images/explosions/explosion1_4.png"
    ]

level1.sprite_collections["explosion2"] = [
    "images/explosions/explosion2_1.png",
    "images/explosions/explosion2_2.png",
    "images/explosions/explosion2_3.png",
    "images/explosions/explosion2_4.png"
    
]


# player

player = Player(parent=level1)
weapon1 = Weapon1(game=game, max_shoot_cooldown=0.1, parent=player)
player.weapon = weapon1
player.vel = 10

level1.player = player

level1.enemies = instantiate_fleet(3, 1050, 70, 100)


level1.enemy_queue.append(instantiate_fleet(3, 1050, 70, 100))



game.levels = [level1]
game.start()