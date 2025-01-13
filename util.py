import asyncio
import collections.abc
import traceback

from . import logger


def maybe_parse_float(input_string: str, maybe: float) -> float:
    try:
        return float(input_string)
    except (ValueError, OverflowError):
        logger.error_log("Failed to parse float in maybe_parse_float", traceback.format_exc())
        return maybe

#Allows running an async function on a thread
def start_async(function: collections.abc.Callable) -> None:
    asyncio.run(function())
