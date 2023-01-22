def ordinal(n: int) -> str:
    if n < 0:
        raise ValueError('Negative ordinal - ordinal must be passed a non-negative integer.')

    if n%100 in (11, 12, 13): return f'{n}th'
    if n%10 == 1: return f'{n}st'
    if n%10 == 2: return f'{n}nd'
    if n%10 == 3: return f'{n}rd'
    return f'{n}th'
