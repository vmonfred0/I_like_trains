"""
Game class for the game "I Like Trains"
"""

import random
import threading
import time

from common.server_config import ServerConfig
from server.train import Train
from server.passenger import Passenger
import logging
from server.delivery_zone import DeliveryZone
from server.high_score import HighScore


# Use the logger configured in server.py
logger = logging.getLogger("server.game")

ORIGINAL_GAME_WIDTH = 400
ORIGINAL_GAME_HEIGHT = 400

ORIGINAL_GRID_NB = 20

TRAINS_PASSENGER_RATIO = 1.0  # Number of trains per passenger

GAME_SIZE_INCREMENT_RATIO = (
    0.05  # Increment per train, the bigger the number, the bigger the screen grows
)
CELL_SIZE = int(ORIGINAL_GAME_WIDTH / ORIGINAL_GRID_NB)
GAME_SIZE_INCREMENT = int(
    ((ORIGINAL_GAME_WIDTH + ORIGINAL_GAME_HEIGHT) / 2) * GAME_SIZE_INCREMENT_RATIO
)  # Increment per train

SPAWN_SAFE_ZONE = 3
SAFE_PADDING = 3


def generate_random_non_blue_color():
    """Generate a random RGB color avoiding blue nuances"""
    while True:
        r = random.randint(100, 230)  # Lighter for the trains
        g = random.randint(100, 230)
        b = random.randint(0, 150)  # Limit the blue

        # If it's not a blue nuance (more red or green than blue)
        if r > b + 50 or g > b + 50:
            return (r, g, b)


class Game:
    # TODO(alok): remove nb_players and use config.clients_per_room
    def __init__(self, config: ServerConfig, send_cooldown_notification, nb_players, room_id):
        self.config = config
        self.send_cooldown_notification = send_cooldown_notification
        self.room_id = room_id

        # Calculate initial game size based on number of clients
        self.game_width = ORIGINAL_GAME_WIDTH + (nb_players * GAME_SIZE_INCREMENT)
        self.game_height = ORIGINAL_GAME_HEIGHT + (
            nb_players * GAME_SIZE_INCREMENT
        )

        self.delivery_zone = DeliveryZone(
            self.game_width, self.game_height, CELL_SIZE, nb_players
        )
        self.cell_size = CELL_SIZE

        self.trains = {}
        self.ai_clients = {}
        self.best_scores = {}
        self.train_colors = {}  # {nickname: (train_color, wagon_color)}
        self.passengers = []
        self.dead_trains = {}  # {nickname: death_time}
        self.train_death_ticks = {}  # {nickname: death_tick} - For tick-based cooldown
        self.current_tick = 0  # Current tick counter
        self.start_time_ticks = 0  # Start time in ticks
        self.start_time = None  # Track when the game starts
        self.last_remaining_time = None  # Track the last remaining time sent to clients

        self.desired_passengers = 0

        self.lock = threading.Lock()

        self.game_started = False  # Track if game has started
        self.last_delivery_ticks = {}  # {nickname: last_delivery_tick}
        self.running = True

        # self.high_score_all_time = HighScore()
        # self.high_score_all_time.load() 
        # self.high_score_all_time.dump()

        # Dirty flags for the game
        self._dirty = {
            "trains": True,
            "size": True,
            "cell_size": True,
            "passengers": True,
            "delivery_zone": True,
            "best_scores": True,
        }
        logger.info(f"Game initialized with tick rate: {self.config.tick_rate}")

    def get_state(self):
        """Return game state with only modified data"""
        state = {}

        # Add game dimensions if modified
        if self._dirty["size"]:
            state["size"] = {
                "game_width": self.game_width,
                "game_height": self.game_height,
            }
            self._dirty["size"] = False

        # Add grid size if modified
        if self._dirty["cell_size"]:
            state["cell_size"] = self.cell_size
            self._dirty["cell_size"] = False

        # Add passengers if modified
        if self._dirty["passengers"]:
            state["passengers"] = [p.to_dict() for p in self.passengers]
            self._dirty["passengers"] = False

        # Add modified trains
        trains_data = {}
        for name, train in self.trains.items():
            train_data = train.to_dict()
            if train_data:  # Only add if data has changed
                trains_data[name] = train_data

        # Add delivery zone if modified
        if self._dirty["delivery_zone"]:
            state["delivery_zone"] = self.delivery_zone.to_dict()
            self._dirty["delivery_zone"] = False

        if trains_data:
            state["trains"] = trains_data
            self._dirty["trains"] = False

        # Add best scores if modified
        if self._dirty["best_scores"]:
            state["best_scores"] = self.best_scores
            self._dirty["best_scores"] = False

        return state

    def is_position_safe(self, x, y):
        """Check if a position is safe for spawning"""
        # Check the borders
        safe_distance = self.cell_size * SPAWN_SAFE_ZONE
        if (
            x < safe_distance
            or y < safe_distance
            or x > self.game_width - safe_distance
            or y > self.game_height - safe_distance
        ):
            return False

        # Check other trains and wagons
        for train in self.trains.values():
            # Distance to the train
            train_x, train_y = train.position
            if abs(train_x - x) < safe_distance and abs(train_y - y) < safe_distance:
                return False

            # Distance to wagons
            for wagon_x, wagon_y in train.wagons:
                if (
                    abs(wagon_x - x) < safe_distance
                    and abs(wagon_y - y) < safe_distance
                ):
                    return False

        # Check delivery zone
        delivery_zone = self.delivery_zone
        if (
            x > delivery_zone.x
            and x < delivery_zone.x + delivery_zone.width
            and y > delivery_zone.y
            and y < delivery_zone.y + delivery_zone.height
        ):
            return False

        # Check other passengers
        for passenger in self.passengers:
            if passenger != self and (x, y) == passenger.position:
                return False

        return True

    def get_safe_spawn_position(self, max_attempts=100):
        """Find a safe position for spawning"""
        for _ in range(max_attempts):
            # Position aligned on the grid
            x = (
                random.randint(
                    SPAWN_SAFE_ZONE,
                    (self.game_width // self.cell_size) - SPAWN_SAFE_ZONE,
                )
                * self.cell_size
            )
            y = (
                random.randint(
                    SPAWN_SAFE_ZONE,
                    (self.game_height // self.cell_size) - SPAWN_SAFE_ZONE,
                )
                * self.cell_size
            )

            if self.is_position_safe(x, y):
                return x, y

        # Default position at the center
        center_x = (self.game_width // 2) // self.cell_size * self.cell_size
        center_y = (self.game_height // 2) // self.cell_size * self.cell_size
        logger.warning(f"Using default center position: ({center_x}, {center_y})")
        return center_x, center_y

    def update_passengers_count(self):
        """Update the number of passengers based on the number of trains"""
        # Calculate the desired number of passengers based on the number of alive trains
        self.desired_passengers = (
            len(
                [
                    train
                    for train in self.trains.values()
                    if self.contains_train(train.nickname)
                ] # This is a list of all trains that are still alive in the game
            )
        ) // TRAINS_PASSENGER_RATIO

        # Add or remove passengers if necessary
        changed = False
        while len(self.passengers) < self.desired_passengers:
            new_passenger = Passenger(self)
            self.passengers.append(new_passenger)
            changed = True
            logger.debug("Added new passenger")

        if changed:
            self._dirty["passengers"] = True

    def add_train(self, nickname):
        """Add a new train to the game"""
        logger.debug(f"Adding train {nickname}")
        # Check the cooldown
        if nickname in self.dead_trains:
            del self.dead_trains[nickname]

        # Create the new train
        spawn_pos = self.get_safe_spawn_position()
        if spawn_pos:
            # If the agent name is in the train_colors dictionary, use the color, otherwise generate a random color
            if nickname in self.train_colors:
                train_color = self.train_colors[nickname]
            else:
                train_color = generate_random_non_blue_color()

            self.trains[nickname] = Train(
                spawn_pos[0],
                spawn_pos[1],
                nickname,
                train_color,
                self.handle_train_death,
                self.config.tick_rate,
            )
            self.update_passengers_count()
            return True
        return False

    def send_cooldown(self, nickname, death_reason):
        """Remove a train and update game size"""
        if nickname in self.trains:
            # Register the death time
            # In grading mode, use tick-based cooldown
            self.train_death_ticks[nickname] = self.current_tick
            
            # Calculate the expected respawn tick based on the standard tickrate
            standard_tickrate = 60.0  # Reference tickrate
            tickrate_ratio = standard_tickrate / self.config.tick_rate
            
            # For tickrate < standard (e.g. 30), the ratio > 1, making cooldown longer in real time
            # For tickrate > standard (e.g. 240), the ratio < 1, making cooldown shorter in real time
            adjusted_cooldown_ticks = int(self.config.respawn_cooldown_seconds * self.config.tick_rate * tickrate_ratio)
            expected_respawn_tick = self.current_tick + adjusted_cooldown_ticks
            
            real_seconds = adjusted_cooldown_ticks / self.config.tick_rate
            logger.debug(f"Train {nickname} died at tick {self.current_tick}, reason: {death_reason}")
            logger.debug(f"Expected respawn at tick {expected_respawn_tick} (after {adjusted_cooldown_ticks} ticks, {real_seconds:.2f}s real time)")

            # Clean up the last delivery time for this train
            if nickname in self.last_delivery_ticks:
                del self.last_delivery_ticks[nickname]

            # Notify the client of the cooldown
            self.send_cooldown_notification(
                nickname, self.config.respawn_cooldown_seconds, death_reason
            )
            # If the client is a bot
            if nickname in self.ai_clients:
                # Get the client object
                client = self.ai_clients[nickname]
                # Change the train's state
                client.is_dead = True
                client.death_tick = self.current_tick
                client.waiting_for_respawn = True
                client.respawn_cooldown = self.config.respawn_cooldown_seconds
            return True
        else:
            logger.error(f"Train {nickname} not found in game")
            return False

    def handle_train_death(self, train_nicknames, death_reason):
        """Handle the death of one or more trains"""
        for nickname in train_nicknames:
            train = self.trains.get(nickname)
            if train:
                train.set_alive(False)
                self.send_cooldown(nickname, death_reason)
                self.update_passengers_count()
                train.reset()
            else:
                logger.warning(f"Train {nickname} not found in kill method")

    def get_train_cooldown(self, nickname):
        """Get remaining cooldown time for a train"""
        # In grading mode, use tick-based cooldown
        if nickname in self.train_death_ticks:
            ticks_elapsed = self.current_tick - self.train_death_ticks[nickname]
            
            # Calculate adjusted cooldown ticks
            standard_tickrate = 60.0  # Reference tickrate
            tickrate_ratio = standard_tickrate / self.config.tick_rate
            adjusted_cooldown_ticks = int(self.config.respawn_cooldown_seconds * self.config.tick_rate * tickrate_ratio)
            
            remaining_ticks = max(0, adjusted_cooldown_ticks - ticks_elapsed)
            # Return remaining ticks as seconds for consistency
            return remaining_ticks / self.config.tick_rate
        return 0

    def contains_train(self, nickname):
        """Check if a train is in the game"""
        return nickname in self.trains

    def check_collisions(self):
        # Créer une copie du dictionnaire pour éviter de le modifier pendant l'itération
        trains_copy = list(self.trains.items())
        for _, train in trains_copy:
            train.update(
                self.trains,
                self.game_width,
                self.game_height,
                self.cell_size,
            )

            # Check for passenger collisions
            for passenger in self.passengers:
                if train.position == passenger.position:
                    train.add_wagons(nb_wagons=passenger.value)

                    desired_passengers = (len(self.trains)) // TRAINS_PASSENGER_RATIO
                    if len(self.passengers) <= desired_passengers:
                        passenger.respawn()
                    else:
                        # Remove the passenger from the passengers list if there are too many
                        self.passengers.remove(passenger)
                        self._dirty["passengers"] = True

            # Check for delivery zone collisions
            if self.delivery_zone.contains(train.position):
                # Check if enough ticks have passed since the last delivery for this train
                if (
                    train.nickname not in self.last_delivery_ticks
                    or self.current_tick - self.last_delivery_ticks.get(train.nickname, 0)
                    >= self.get_delivery_cooldown_ticks()
                ):
                    # Slowly popping wagons and increasing score
                    wagon = train.pop_wagon()
                    if wagon:
                        train.update_score(train.score + 1)
                        # Update best score if needed
                        if train.score > self.best_scores.get(train.nickname, 0):
                            self.best_scores[train.nickname] = train.score
                            self._dirty["best_scores"] = True
                        # Update the last delivery tick for this train
                        self.last_delivery_ticks[train.nickname] = self.current_tick

    def get_delivery_cooldown_ticks(self):
        standard_tickrate = 60.0  # Reference tickrate
        tickrate_ratio = standard_tickrate / self.config.tick_rate
        adjusted_cooldown_ticks = int(self.config.delivery_cooldown_seconds * self.config.tick_rate * tickrate_ratio)
        return adjusted_cooldown_ticks

    def update(self):
        """Update game state"""
        if not self.trains:  # Update only if there are trains
            return

        with self.lock:
            # Update all trains and check for death conditions
            # trains_to_remove = []
            self.check_collisions()

            # Check for train deaths based on tick counter
            death_ticks_to_check = self.train_death_ticks.copy()
            for nickname, death_tick in death_ticks_to_check.items():
                # Calculate the respawn cooldown with adjustment for game speed
                standard_tickrate = 60.0  # Reference tickrate
                tickrate_ratio = standard_tickrate / self.config.tick_rate
                
                # Calculate cooldown ticks with proper adjustment for game speed
                adjusted_cooldown_ticks = int(self.config.respawn_cooldown_seconds * self.config.tick_rate * tickrate_ratio)
                
                if self.current_tick >= death_tick + adjusted_cooldown_ticks:
                    real_time_elapsed = (self.current_tick - death_tick) / self.config.tick_rate
                    logger.info(f"Train {nickname} cooldown expired at tick {self.current_tick} (after {self.current_tick - death_tick} ticks, {real_time_elapsed:.2f}s real time)")
                    
                    # Remove from death ticks dictionary
                    if nickname in self.train_death_ticks:
                        del self.train_death_ticks[nickname]
                    
                    # If the train is an AI, handle respawn
                    if nickname in self.ai_clients:
                        ai_client = self.ai_clients[nickname]
                        if ai_client.is_dead and ai_client.waiting_for_respawn:
                            logger.info(f"Respawning AI client {nickname} after cooldown")
                            if self.add_train(nickname):
                                ai_client.waiting_for_respawn = False
                                ai_client.is_dead = False
                                logger.debug(f"AI client {nickname} respawned after cooldown")

            # Handle automatic respawn for AI clients
            for ai_name, ai_client in self.ai_clients.items():
                # Add automatic respawn logic
                if ai_client.is_dead and ai_client.waiting_for_respawn:
                    if ai_client.in_waiting_room:
                        logger.debug(
                            f"AI client {ai_name} in waiting room, trying to start game"
                        )
                        # Start game if in waiting room
                        if (
                            not ai_client.room.game_thread
                            or not ai_client.room.game_thread.is_alive()
                        ):
                            if ai_client.room.get_player_count() >= ai_client.room.nb_players_max:
                                ai_client.room.start_game()

                    cooldown = self.get_train_cooldown(ai_name)
                    if cooldown <= 0:
                        if self.add_train(ai_name):
                            ai_client.waiting_for_respawn = False
                            ai_client.is_dead = False
                            logger.info(f"AI client {ai_name} respawned")

                # Update agent state only if train is alive and game contains train
                else:
                    # Call the update_cycle method directly instead of updating manually
                    ai_client.update_state()
