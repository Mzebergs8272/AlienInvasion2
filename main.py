from AlienInvasion import Game, Level, Ship, Player, Weapon, Weapon1, StandardEnemy


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
            random_shoot_cooldowns=kwargs.get("random_shoot_cooldowns", [1, 1,5, 2, 2.5, 3])

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
player: Ship = Player(level1, parent=level1, vel=10, sprite_collection_name="explosion2")
weapon1: Weapon = Weapon1(level1, parent=player, max_shoot_cooldown=0.1, round_sprite_collection_name="explosion1")
player.weapon = weapon1

level1.player = player

level1.enemy_queue = [instantiate_fleet(level1, 3, 1050, 70, 100), 
                      instantiate_fleet(level1, 3, 1050, 70, 100)]

game.levels = [level1]
game.start()