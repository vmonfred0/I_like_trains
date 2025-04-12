# Project Structure

The project is divided into two main parts:

## 1. Server (folder `server/`)
The server is responsible for managing client connections and game synchronization. It is executed on a remote machine you can connect to.
The server files are included here so you can have a better understanding of how the management of the game works. 

- `server.py` : Manages client connections and game synchronization.
- `game.py` : Contains the main game logic. Each train moves by self.cell_size each time the get_move() method is called.
- `train.py` : Defines the Train class and its behaviors. 
- `passenger.py` : Manages passenger logic.
- `ai_client.py` : Manages AI clients (when a player disconnects).
- `delivery_zone.py` : Manages delivery zones.

## 2. Client (folder `client/`)
The client is responsible for managing the game display and user interactions. It is executed on your machine when executing `client/client.py`.

- `client.py` : Manages server connection and the main game loop.
- `network.py` : Manages network communication with the server.
- `renderer.py` : Responsible for the graphical display of the game.
- `event_handler.py` : Manages events (keyboard inputs).
- `game_state.py` : Maintains the game state on the client side.
- `ui.py` : Manages the user interface to enter train name and sciper.

## 3. Agents (folder `common/agents/`)
The agents are the files that control the behavior of the train. You can find the implementation of the `BaseAgent` class in `common/base_agent.py`. 

The agents are stored in the `common/agents` folder. You can add your own agent by creating a new file in this folder. The agent file should contain a class that inherits from the `BaseAgent` class and implements the `get_move()` method. You can name them as you want and import them in the config to test them.

## How the client data is updated from the server

1. The server hosts the room and calculates the **game state** (information from the server about the game, like the trains positions, the passengers, the delivery zones, etc.)
2. The client connects to the remote server (by default on localhost:5555)
3. The client sends its **train name** and **sciper** to the server
4. The server regularly sends the game state to the clients, and also listens to potential actions (change direction or drop wagon) from the clients to influence the game.
5. The client receives the game state in the `network.py` and updates the agent's game state from the `handle_state_data()` method in `game_state.py`.
6. This method then calls `update_agent()` (inherited by the `Agent` class from the `BaseAgent` class) to ask for a new direction the agent has to determine.
7. The `update_agent()` method then calls the method `get_move()` to dynamically calculate the next direction the train should take according to the game state (where are the other trains, the walls, the passengers, the delivery zones, etc.) and send it to the server.
8. The server updates the game state and the cycle continues.
