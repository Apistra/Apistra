"""Allowed cyclomatic-complexity control sample."""


def classify(value: int) -> str:
    if value < 0:
        return "negative"
    if value == 0:
        return "zero"
    return "positive"
