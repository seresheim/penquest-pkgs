import asyncio
import json

from typing import Any


async def parse_stream(reader: asyncio.StreamReader):
    try:
        while not reader.at_eof():
            encoded_msg = await reader.readline()
            if encoded_msg is None: break
            str_msg = encoded_msg.decode('utf-8').rstrip("\n")
            if str_msg == "": break
            parsed_msg = json.loads(str_msg)
            yield parsed_msg
    finally:
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
