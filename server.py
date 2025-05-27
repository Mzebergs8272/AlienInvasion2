import asyncio
import websockets
import json
from websockets import WebSocketClientProtocol

connected_clients: dict[int, dict[str, object]] = {}

# runs for every time a client connects to the websocket
async def handler(websocket: WebSocketClientProtocol):
    
    user_id = json.loads(await websocket.recv())["id"]


    connected_clients.update({user_id: {"websocket": websocket}})

    print(f"User {user_id} connected")
   
    try:
        async for message in websocket:    
           print(f"user {user_id}:", json.loads(message))

           await asyncio.gather(*(client_data["websocket"].send(message) for id, client_data in connected_clients.items() if id != user_id))
           
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        connected_clients.pop(user_id)


async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("Server started on port 8765")
        await asyncio.Future() # run forever

asyncio.run(main())