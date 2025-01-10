def try_parse_float(input_string):
    try:
        return float(input_string)
    except Exception:
        return None
