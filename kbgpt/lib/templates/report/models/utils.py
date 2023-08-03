__all__ = ["round"]


builtin_round = round


def round(dat: float, dits: int):  # pylint: disable=redefined-builtin
    return (
        0.01
        if dat > 0 and dat <= 0.01
        else -0.01
        if dat >= -0.01 and dat < 0
        else builtin_round(dat, dits)
    )
