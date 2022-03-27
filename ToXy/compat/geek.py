

def compat(code: str) -> str:
    """Reformats modules, built for GeekTG to work with ToXy"""
    code = code.replace("GeekInlineQuery", "InlineQuery")

    return code
