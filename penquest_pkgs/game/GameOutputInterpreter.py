import asyncio
from typing import Tuple, Any, Union, Dict

from penquest_pkgs.constants.Events import Events
from penquest_pkgs.utils.ios import write_stream, write_queue
from penquest_pkgs.utils.logging import get_logger



class GameOutputInterpreter:

    """Translates SEND events to outgoing messages and sends them to the
    websocket process.
    """

    def __init__(
            self, 
            output_channel: Union[asyncio.StreamWriter, asyncio.Queue], 
            game= None
        ):
        """Initializes all attributes

        :param output_channel: channel that is connected to the websocket process
        :param game: game instance for start listening, defaults to None
        """
        self.output_channel = output_channel
        self.game = game
        logger = self.game.logger if self.game is not None else get_logger(__name__)
        if isinstance(output_channel, asyncio.StreamWriter):
            self.send_func = write_stream
            logger.debug("Detected StreamWriter as send channel")
        elif isinstance(output_channel, asyncio.Queue):
            self.send_func = write_queue
            logger.debug("Detected Queue as send channel")
        

    async def reroute_game_send_event(
            self,
            event: str,
            data: Tuple[str, str, Dict]
        ) -> Tuple[bool, Any]:
        """Reroutes an incoming SEND event to the websocket process

        :param event: incoming event
        :param data: tuple of the form (connection_id, message_type, data)
        :return: True, None
        """
        if event != Events.SEND: return False, None
        command = None
        if data is not None and len(data) == 3 and data[2] is not None:
            command = data[2].get("event", None)
        logger = self.game.logger if self.game is not None else get_logger(__name__)
        logger.debug(f"Sending command '{command}'")
        await self.send_func(data, self.output_channel)
        return True, None

    async def start_listening(self, game = None):
        """Starts the SEND event forwarding

        :param game: instance of the game, defaults to None
        """
        self.game = game
        if self.game is None: return
        self.game.event_listener.append(self.reroute_game_send_event)
