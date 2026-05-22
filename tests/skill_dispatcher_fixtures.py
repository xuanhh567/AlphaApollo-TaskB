def echo_tool(text: str, count: int = 1):
    return {"text_result": text * count, "score": 1}


def value_tool(text: str, count: int = 1):
    return {"value": text}


def failing_tool(text: str, count: int = 1):
    raise RuntimeError(f"boom: {text}")


NOT_CALLABLE = "not callable"
