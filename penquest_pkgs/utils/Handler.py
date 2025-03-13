import asyncio
from typing import Optional, Dict, List, Any, Callable, Tuple, Awaitable, Union


EventListener = Callable[[str, Dict[str, Any]], Awaitable[Tuple[bool, Any]]]


class EventBasedObject:
    event_listener: List[EventListener]
    
    def __init__(self) -> None:
        self.event_listener = []


    async def dispatch_event(self, event: str, data: Any = None, default_return = None) -> Optional[Any]:
        """
        Forwards an event to all event listeners
        :param event: str - Event to dispatch
        :param data: Any - Data to send with the event
        :param default_return: Any - Default return value if no event listener is registered
        :return: Any - Return value of the event listener
        """

        # Run all event listeners
        for listener in self.event_listener:
            finished, ret = await listener(event, data)
            if finished: return ret

        return default_return
    

    async def await_event(self, event_or_events: Union[str, List[str]], timeout: Optional[float] = 30):
        """
        Awaits until either a single event or one of multiple events is received

        :param event: str - Event to await
        :param timeout: float - Timeout in seconds
        :return: Any - Return value of the event listener
        """

        if isinstance(event_or_events, str):
            event_or_events = [event_or_events]

        reply = asyncio.Future()
        async def listener(_event, _data):
            if _event not in event_or_events: return False, None
            reply.set_result(_data)
            return True, None 
        self.event_listener.append(listener)

        try:
            return await asyncio.wait_for(reply, timeout)
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(
                f"Timeout reached while waiting for event: "
                f"{', '.join(event_or_events)}"
            )
        finally:
            self.event_listener.remove(listener)

    async def await_events(
            self, 
            events: List[str], 
            timeout: Optional[float]=30
        ):
        """Awaits multiple events after each other. The order of the events is
        important as events have to appear in the order as they are given to
        this function and 'a little' time needs to appear between them.

        :param events: _description_
        :param timeout: _description_, defaults to 30
        """
        # 'a little time' is requried between the events in order for asyncio
        # this corouting again.
        replies = []
        event_listeners = {}


        for event in events:
            reply = asyncio.Future()
            replies.append(reply)
            async def listener(_event, _data):
                if _event not in [event]: return False, None
                reply.set_result(_data)
                return True, None 
            self.event_listener.append(listener)
            event_listeners[event] = listener

        try:
            ret_value = None
            for event, reply in zip(events, replies):
                ret_value = await asyncio.wait_for(reply, timeout)
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(
                f"Timeout reached while waiting for event: '{event}'"
            )
        finally:
            for event in events:
                self.event_listener.remove(event_listeners[event])
            return ret_value