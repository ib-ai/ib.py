def ordinal(n: int) -> str:
    match n%10:
        case 1:
            return f'{n}st'
        case 2:
            return f'{n}nd'
        case 3:
            return f'{n}rd'
        case _:
            return f'{n}th'