import asyncio
import json

from typing import Any

from penquest_pkgs.utils.logging import get_logger


async def parse_stream(reader: asyncio.StreamReader):
    try:
        while not reader.at_eof():
            encoded_msg = await reader.readline()
            if encoded_msg is None: 
                get_logger(__name__).debug(
                    "received None message in parse_stream coming"
                )
                break
            str_msg = encoded_msg.decode('utf-8').rstrip("\n")
            if str_msg == "": 
                get_logger(__name__).debug(
                    "received empty string message in parse_stream coming"
                )
                break
            parsed_msg = json.loads(str_msg)
            yield parsed_msg
    except Exception as e:
        get_logger(__name__).error(
            f"Error in parse_stream: {e}"
        )
    finally:
        if not reader.at_eof():
            get_logger(__name__).debug(
                "feeding eof to the reader in parse_stream"
            )
            reader.feed_eof()

async def parse_queue(queue: asyncio.Queue):
    while True:
        msg = await queue.get()
        if msg is None: break
        yield msg

async def write_stream(msg: Any, writer: asyncio.StreamWriter):
    str_msg = json.dumps(msg)+"\n"
    encoded_msg = bytes(str_msg, 'utf-8')
    writer.write(encoded_msg)
    await writer.drain()

async def write_queue(msg: Any, queue: asyncio.Queue):
    queue.put_nowait(msg)
