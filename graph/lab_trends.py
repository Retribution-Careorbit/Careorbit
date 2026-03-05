LOWER_IS_BETTER = {
    "4548-4",
    "2160-0",
    "2093-3",
    "2571-8",
    "13457-7",
    "1751-7",
    "14749-6",
}

HIGHER_IS_BETTER = {
    "33914-3",
    "2085-9",
    "718-7",
    "787-2",
}


def calculate_trend(values: list, loinc_code: str) -> dict:
    if len(values) < 2:
        return {"direction": "insufficient_data"}

    first = values[0]
    last = values[-1]
    diff = last - first

    threshold = abs(first) * 0.02 if first != 0 else 0.01
    if abs(diff) < threshold:
        return {"direction": "stable"}

    value_going_up = diff > 0
    value_going_down = diff < 0

    if loinc_code in LOWER_IS_BETTER:
        if value_going_down:
            return {"direction": "improving"}
        else:
            return {"direction": "worsening"}
    elif loinc_code in HIGHER_IS_BETTER:
        if value_going_up:
            return {"direction": "improving"}
        else:
            return {"direction": "worsening"}
    else:
        if value_going_up:
            return {"direction": "worsening"}
        else:
            return {"direction": "improving"}
