import asyncio
import collections.abc
import logging


def maybe_parse_float(input_string: str, maybe: float) -> float:
    try:
        return float(input_string)
    except (ValueError, OverflowError):
        logging.exception("Failed to parse float in maybe_parse_float")
        return maybe

#Allows running an async function on a thread
def start_async(function: collections.abc.Callable) -> None:
    asyncio.run(function())
