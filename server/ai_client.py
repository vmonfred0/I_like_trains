"""
AI client for the game "I Like Trains"
This module provides an AI client that can control trains on the server side
"""

import threading
import time
import logging
import json
from server.passenger import Passenger
import importlib


logger = logging.getLogger("server.ai_client")


class AINetworkInterface:
    """
    Mimics the NetworkManager class from the client but directly interacts with
    the game on the server side.
    """

    def __init__(self, room, nickname):
        self.room = room
        self.nickname = nickname

    def send_direction_change(self, direction):
        """Change the direction of the train using the server's function"""
        if self.room.game.contains_train(
            self.nickname
        ):
            self.room.game.trains[self.nickname].change_direction(direction)
            return True
        else:
            logger.error(
                f"Failed to change direction for train {self.nickname}. Train is in game: {self.nickname in self.room.game.trains}"
            )
        return False

    def send_drop_wagon_request(self):
        """Drop a wagon from the train using the server's function"""
        if self.nickname in self.room.game.trains and self.room.game.contains_train(
            self.nickname
        ):
            last_wagon_position = self.room.game.trains[self.nickname].drop_wagon()
            if last_wagon_position:
                # Create a new passenger at the position of the dropped wagon
                new_passenger = Passenger(self.room.game)
                new_passenger.position = last_wagon_position
                new_passenger.value = 1
                self.room.game.passengers.append(new_passenger)
                self.room.game._dirty["passengers"] = True
                return True
        return False

    def send_spawn_request(self):
        """Request to spawn the train using the server's function"""
        logger.debug(f"AI client {self.nickname} sending spawn request")
        if self.nickname not in self.room.game.trains:
            cooldown = self.room.game.get_train_respawn_cooldown(self.nickname)
            if cooldown <= 0:
                return self.room.game.add_train(self.nickname)
        return False


class AIClient:
    """
    AI client that controls a train on the server side
    using the Agent class from the client
    """

    def __init__(self, room, nickname, ai_agent_file_name=None, waiting_for_respawn=False, is_dead=False):
        """Initialize the AI client"""
        logger.debug(f"Initializing AI client {nickname}, waiting_for_respawn: {waiting_for_respawn}, is_dead: {is_dead}")
        self.room = room
        self.game = room.game
        self.nickname = nickname  # The AI agent name

        self.is_dead = is_dead
        self.waiting_for_respawn = waiting_for_respawn
        self.death_time = 0
        self.respawn_cooldown = 0

        # Create network interface
        self.network = AINetworkInterface(
            room, nickname
        )  # Use AI name for network interface

        # Initialize agent if path_to_agent is provided
        try:
            logger.info(f"Trying to import AI agent for {nickname}")
            if ai_agent_file_name.endswith(".py"):
                # Remove .py extension
                ai_agent_file_name = ai_agent_file_name[:-3]

            # Construct the module path correctly
            module_path = f"common.agents.{ai_agent_file_name}"
            logger.info(f"Importing module: {module_path}")

            module = importlib.import_module(module_path)
            self.agent = module.Agent(nickname, self.network, logger="server.ai_agent")
            logger.info(f"AI agent {nickname} initialized using {ai_agent_file_name}")

        except ImportError as e:
            logger.error(f"Failed to import AI agent for {nickname}: {e}")
            raise e
        except Exception as e:
            logger.error(f"Failed to import AI agent for {nickname}: {e}")
            raise e

        self.agent.delivery_zone = self.game.delivery_zone.to_dict()

        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"AI client {nickname} started")

        self.update_state()

    def update_state(self):
        """Update the state from the game"""
        # Get the serialized state data from the game
        state_data = self.game.get_state()
        
        # Simuler la sérialisation/désérialisation JSON pour garantir le même format de données
        # que les clients normaux (conversion des tuples en listes, etc.)
        state_data_json = json.dumps(state_data)
        state_data = json.loads(state_data_json)
        
        # Initialize collections if they don't exist yet
        if not hasattr(self, "all_trains") or self.all_trains is None:
            self.all_trains = {}
        if not hasattr(self, "passengers") or self.passengers is None:
            self.passengers = []
        if not hasattr(self, "delivery_zone") or self.delivery_zone is None:
            self.delivery_zone = []
        if not hasattr(self, "cell_size") or self.cell_size is None:
            self.cell_size = None
        if not hasattr(self, "game_width") or self.game_width is None:
            self.game_width = None
        if not hasattr(self, "game_height") or self.game_height is None:
            self.game_height = None
        if not hasattr(self, "best_scores") or self.best_scores is None:
            self.best_scores = []

        # Process the state data similar to GameState.handle_state_data
        
        # Update trains if present in the state data
        if "trains" in state_data:
            for nickname, train_data in state_data["trains"].items():
                if nickname not in self.all_trains:
                    self.all_trains[nickname] = {}
                # Update the modified attributes
                self.all_trains[nickname].update(train_data)
        
        # Update passengers if present
        if "passengers" in state_data:
            self.passengers = state_data["passengers"]
        
        # Update delivery zone if present
        if "delivery_zone" in state_data:
            self.delivery_zone = state_data["delivery_zone"]
        
        # Update size if present
        if "size" in state_data:
            self.game_width = state_data["size"]["game_width"]
            self.game_height = state_data["size"]["game_height"]
        
        # Update cell size if present
        if "cell_size" in state_data:
            self.cell_size = state_data["cell_size"]
        
        # Update best scores if present
        if "best_scores" in state_data:
            self.best_scores = state_data["best_scores"]
            
        # Update other properties
        self.in_waiting_room = not self.game.game_started
        
        # Make sure the agent has access to the correct properties
        self.agent.all_trains = self.all_trains
        self.agent.passengers = self.passengers
        self.agent.cell_size = self.cell_size
        self.agent.best_scores = self.best_scores
        self.agent.game_width = self.game_width
        self.agent.game_height = self.game_height
        self.agent.delivery_zone = self.delivery_zone if hasattr(self, "delivery_zone") else self.game.delivery_zone.to_dict()
        
        # Update agent state only if train is alive and game contains train
        if not self.is_dead and self.game.contains_train(self.nickname):
            self.agent.update_agent()

    def run(self):
        """Main AI client loop"""
        while self.running and self.room.running:
            # Execute a single update cycle
            self.update_state()
            
            # Sleep to avoid high CPU usage
            time.sleep(0.1)

    def stop(self):
        """Stop the AI client"""
        self.running = False
