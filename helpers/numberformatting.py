def abbreviate_number(number: int) -> str:
    if number < 1000:
        return str(int(number))
    elif number < 1000000:
        return f"{format(number / 1000, '.1f')}k"
    elif number < 1000000000:
        return f"{format(number / 1000000, '.1f')}M"


def abbreviate_number_no_dec(number: int) -> str:
    if number < 1000:
        return str(int(number))
    elif number < 1000000:
        return f"{int(number / 1000)}k"
    elif number < 1000000000:
        return f"{int(number / 1000000)}M"
