import asyncio

def try_parse_float(input_string):
    try:
        return float(input_string)
    except Exception:
        return None

#Allows running an async function on a thread
def start_async(function):
    asyncio.run(function())
