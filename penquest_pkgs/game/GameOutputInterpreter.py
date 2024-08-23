import asyncio
from typing import Tuple, Any, Union, Callable, Awaitable

from penquest_pkgs.constants.Events import Events
from penquest_pkgs.utils.ios import write_stream, write_queue
from penquest_pkgs.utils.logging import get_logger



class GameOutputInterpreter:

    """Translates SEND events to outgoing messages and sends them to the
    websocket process.
    """

    def __init__(
            self, 
            send_channel: Union[asyncio.StreamWriter, asyncio.Queue], 
            game= None
        ):
        """Initializes all attributes

        :param send_channel: channel that is connected to the websocket process
        :param game: game instance for start listening, defaults to None
        """
        self.send_channel = send_channel
        if isinstance(send_channel, asyncio.StreamWriter):
            self.send_func = write_stream
            get_logger(__name__).debug("Detected StreamWriter as send channel")
        elif isinstance(send_channel, asyncio.Queue):
            self.send_func = write_queue
            get_logger(__name__).debug("Detected Queue as send channel")
        self.game = game

    async def reroute_game_send_event(
            self,
            event: str,
            data: dict
        ) -> Tuple[bool, Any]:
        """Reroutes an incoming SEND event to the websocket process

        :param event: incoming event
        :param data: data connected to the incoming event
        :return: True, None
        """
        if event != Events.SEND: return False, None
        await self.send_func(data, self.send_channel)
        return True, None

    async def start_listening_to_game_events(self, game = None):
        """Starts the SEND event forwarding

        :param game: instance of the game, defaults to None
        """
        self.game = game
        if self.game is None: return
        self.game.event_listener.append(self.reroute_game_send_event)
