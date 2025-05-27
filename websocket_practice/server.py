import asyncio
import websockets
import json
from websockets import WebSocketClientProtocol

id1 = "1"
id2 = "2"

connected_clients: dict[int, dict[str, WebSocketClientProtocol]] = {
    id1: {},
    id2: {}

}

clients_connected: bool = False

def check_clients_connected():
    if not connected_clients.get(id1) or not connected_clients.get(id2):
        return False
    return True


# runs for every time a client connects to the websocket
async def handler(websocket: WebSocketClientProtocol):
    user_id = None
    if connected_clients[id1] and connected_clients[id2]:
        print("max clients reached")

    if connected_clients[id1]:
        connected_clients[id2].update({"websocket": websocket})
        user_id = id2

        await websocket.send(json.dumps({
            id2: 
            {
                "x": 50,
                "y": 150  
            },
            id1: 
            {
                "x": 50,
                "y": 50     
            },
        }))
    else:
        connected_clients[id1].update({"websocket": websocket})
        user_id = id1

        await websocket.send(json.dumps({
            id1: 
            {
                "x": 50,
                "y": 50     
            },
            id2: 
            {
                "x": 50,
                "y": 150  
            },
        }))

    print(f"User {user_id} connected")

    while not check_clients_connected():
        print("waiting for clients to connect.")
        await asyncio.sleep(1)

    await websocket.send("True")

    try:
        async for message in websocket:    
            print(f"user {user_id}:", json.loads(message))
            
            await asyncio.gather(*(client_data["websocket"].send(message) for id, client_data in connected_clients.items() if client_data and id != user_id))
           
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        connected_clients.pop(user_id)


async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("Server started on port 8765")
        await asyncio.Future() # run forever

asyncio.run(main())