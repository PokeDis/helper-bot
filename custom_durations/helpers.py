from durations_nlp import Duration
from durations_nlp.exceptions import ScaleFormatError


def valid_duration(representation):
    try:
        Duration(representation)
    except ScaleFormatError:
        return False

    return True
