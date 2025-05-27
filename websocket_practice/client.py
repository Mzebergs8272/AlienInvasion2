import pygame as pg, websockets, asyncio, json, random, threading, math
from websockets import WebSocketClientProtocol



class Client:
    def __init__(self): 
        self.id: str = None
        self.other_player_id: str = None
        self.server: WebSocketClientProtocol = None
        self.uri: str = "ws://109.147.61.116:8765"

        self.player_actions_reset = {}

        self.player_actions: dict[str, dict[str, object]] = {}

        self.connected = False

    async def run(self):
        async with websockets.connect(self.uri) as self.server:
            # get player IDs and player actions template
            self.player_actions = json.loads(await self.server.recv())
            self.id = list(self.player_actions.keys())[0]            
            self.other_player_id = list(self.player_actions.keys())[1]

            self.connected = bool(await self.server.recv())

            while True:
                
                if self.player_actions: 
                    await self.server.send(json.dumps(self.player_actions[self.id]))
                msg = await self.server.recv()

                print("message", msg)
                self.player_actions[self.other_player_id] = json.loads(msg)

screen = pg.display.set_mode([500, 500])
clock = pg.time.Clock()

enemies: dict[str, pg.Rect] = {}
players: dict[str, pg.Rect] = {
    0: None,
    1: None
}
client = Client()


def move_to_cursor():
    mouse_pos = pg.mouse.get_pos()
    player_pos = [players[client.id].x + players[client.id].width//2, players[client.id].y + players[client.id].height//2]
    adj = mouse_pos[0] - player_pos[0]
    opp = mouse_pos[1] - player_pos[1]
    hyp = math.sqrt(adj ** 2 + opp ** 2)

    if hyp != 0:
        sin = opp / hyp
        cos = adj / hyp

        # multiply each ratio by hyp. because the further the cursor (and the longer the hyp), 
        # the faster the ship
        players[client.id].x += cos * hyp * 0.35
        players[client.id].y += sin * hyp * 0.35


pg.init()

thread = threading.Thread(target=asyncio.run(client.run()), daemon=True)
thread.start()

player2_colour = (255, 0, 0)
player1_colour = (255, 0, 0)

while True:
    screen.fill("black")
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()

    keys = pg.key.get_pressed()
    
    if not client.connected: 
        if client.id and not players.get(client.id):
            players.pop(0)
            players[client.id] = pg.Rect(50, 50, 50, 50)
        
        if client.other_player_id and not players.get(client.other_player_id):
            players.pop(1)
            players[client.other_player_id] = pg.Rect(50, 50, 50, 50)

        continue

    move_to_cursor()

    if client.player_actions and client.id and client.other_player_id:
        player1_colour = (255, 0, 0)
        if keys[pg.K_SPACE]:
            client.player_actions[client.id]["is_shooting"] = True
            player1_colour = (0, 0, 255)
        else:
            client.player_actions[client.id]["is_shooting"] = False

        client.player_actions[client.id]["x"] = players[client.id].x
        client.player_actions[client.id]["y"] = players[client.id].y

        players[client.other_player_id].x = client.player_actions[client.other_player_id]["x"]
        players[client.other_player_id].y = client.player_actions[client.other_player_id]["y"]

        player2_colour = (255, 0, 0)
        if client.player_actions[client.other_player_id].get("is_shooting"):
            player2_colour = (0, 0, 255)
            
        pg.draw.rect(screen, player2_colour, players[client.other_player_id])

        pg.draw.rect(screen, player1_colour, players[client.id])
    
    pg.display.update()
    clock.tick(60)

