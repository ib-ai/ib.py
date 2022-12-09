def ordinal(n: int) -> str:
    if n < 0:
        raise ValueError('Negative ordinal - ordinal must be passed a non-negative integer.')

    match n//10 % 10:  # for numbers trailing with 11, 12, or 13
        case 1:
            return f'{n}th'
    match n%10:
        case 1:
            return f'{n}st'
        case 2:
            return f'{n}nd'
        case 3:
            return f'{n}rd'
        case _:
            return f'{n}th'