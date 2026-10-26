def format_currency(amount):
    """Format an application amount in South African rand."""
    return f"R {float(amount or 0):,.2f}"