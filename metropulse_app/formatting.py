def format_number(value, decimals=0):
    if value is None:
        return "—"

    return f"{value:,.{decimals}f}"


def format_currency(value, decimals=2):
    if value is None:
        return "—"

    return f"${value:,.{decimals}f}"


def format_percentage(value, decimals=1):
    if value is None:
        return "—"

    return f"{value:.{decimals}f}%"


def format_minutes(value, decimals=1):
    if value is None:
        return "—"

    return f"{value:.{decimals}f} min"


def format_distance(value, decimals=2):
    if value is None:
        return "—"

    return f"{value:,.{decimals}f} mi"


def format_speed(value, decimals=1):
    if value is None:
        return "—"

    return f"{value:.{decimals}f} mph"