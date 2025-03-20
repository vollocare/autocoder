def get_greeting(name: str = "World") -> str:
    """
    Generates a personalized greeting.

    Args:
        name (str): The name of the person to greet. Defaults to "World".

    Returns:
        str: A personalized greeting message.

    Raises:
        ValueError: If the name contains invalid Unicode characters.
    """
    if not all(c.isprintable() for c in name):
        raise ValueError("Invalid characters in name.")
    
    return f"Hello, {name}!"