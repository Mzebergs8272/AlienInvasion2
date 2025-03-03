from AlienInvasion import Game, Level, Player, Weapon1, StandardEnemy



game = Game()
level1 = Level(parent=game)


# player
weapon1 = Weapon1(max_shoot_cooldown=0.1, parent=game)
player = Player(parent=level1, weapon=weapon1)
player.vel = 10
weapon1.parent = player
level1.player = player


def instantiate_enemies():
    global enemy1, enemy2, enemy3, enemy4
    # enemies
    enemy_weapon1 = Weapon1(max_shoot_cooldown=0, parent=game)
    enemy1 = StandardEnemy(level1, enemy_weapon1, [1050, 70])
    enemy1.random_shoot_cooldowns = [1, 1,5, 2, 2.5, 3]
    enemy_weapon1.parent = enemy1

    enemy_weapon2 = Weapon1(max_shoot_cooldown=0, parent=game)
    enemy2 = StandardEnemy(level1, enemy_weapon2, [1050, 190])
    enemy2.random_shoot_cooldowns = [1, 1,5, 2, 2.5, 3]
    enemy_weapon2.parent = enemy2

    enemy_weapon3 = Weapon1(max_shoot_cooldown=0, parent=game)
    enemy3 = StandardEnemy(level1, enemy_weapon3, [1050, 310])
    enemy3.random_shoot_cooldowns = [1, 1, 5, 2, 2.5, 3]
    enemy_weapon3.parent = enemy3

    enemy_weapon4 = Weapon1(max_shoot_cooldown=0, parent=game)
    enemy4 = StandardEnemy(level1, enemy_weapon4, [1050, 430])
    enemy4.random_shoot_cooldowns = [1, 1,5, 2, 2.5, 3]
    enemy_weapon4.parent = enemy4

instantiate_enemies()

level1.enemies = [enemy1, enemy2, enemy3, enemy4]
level1.sprite_collections["explosion1"] = [
    "images/explosions/explosion1_1.png",
    "images/explosions/explosion1_2.png",
    "images/explosions/explosion1_3.png",
    "images/explosions/explosion1_4.png"
    ]


instantiate_enemies()
level1.enemy_queue.append([enemy1, enemy2, enemy3, enemy4])
game.levels = [level1]
game.start()