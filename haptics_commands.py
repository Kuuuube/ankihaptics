import asyncio
import threading

from . import util

def run_scalar_command(actuator, start_strength, end_strength, duration):
    threading.Thread(target = lambda: util.start_async(lambda: scalar_command(actuator, start_strength, end_strength, duration)))

async def scalar_command(actuator, start_strength, end_strength, duration):
    await actuator.command(start_strength)
    await asyncio.sleep(duration)
    await actuator.command(end_strength)
