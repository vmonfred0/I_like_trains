import logging
from client.network import NetworkManager
from common import move
import concurrent.futures
from common.constants import REFERENCE_TICK_RATE


class BaseAgent:
    """Base class for all agents, enforcing the implementation of get_move()."""

    def __init__(
        self, nickname: str, network: NetworkManager, logger: str = "client.agent"
    ):
        """
        Initialize the base agent. Not supposed to be modified.

        Args:
            nickname (str): The name of the agent
            network (NetworkManager): The network object to handle communication
            logger (str): The logger name

        Attributes:
            cell_size (int): The size of a cell in pixels
            game_width (int): The width of the game in cells
            game_height (int): The height of the game in cells
            all_trains (dict): Dictionary of all trains in the game
            passengers (list): List of passengers in the game
            delivery_zone (list): List of delivery zones in the game
        """
        self.logger = logging.getLogger(logger)
        self.logger.setLevel(logging.DEBUG)
        self.nickname = nickname
        self.network = network

        # Game parameters, regularly updated by the client in handle_state_data() (see game_state.py)
        self.cell_size = None
        self.game_width = None
        self.game_height = None
        self.all_trains = None
        self.passengers = None
        self.delivery_zone = None
        self.best_scores = None

    def get_move(self):
        """
        Abstract method to be implemented by subclasses.
        Must return a valid move.Move.
        """
        pass

    def update_agent(self):
        """
        Regularly called by the client to send the new direction to the server. Not supposed to be modified.

        Returning from this method without doing anything will cause the train to continue moving forward.
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self.get_move)
            try:
                new_direction = future.result(timeout=1/REFERENCE_TICK_RATE)
            except concurrent.futures.TimeoutError:
                # The agent took too long to respond
                error_msg = f"Agent {self.nickname} too slow! Execution exceeded timeout limit of 1/{REFERENCE_TICK_RATE}s"
                self.logger.error(error_msg)
                return
            except Exception as e:
                self.logger.error(f"get_move() raised an exception: {e}")
                return
            
        if new_direction not in move.Move:
            self.logger.error("get_move() did not return a valid move!")
            return

        if new_direction == move.Move.DROP:
            self.network.send_drop_wagon_request()
            return

        if new_direction != self.all_trains[self.nickname]["direction"]:
            self.network.send_direction_change(new_direction.value)
