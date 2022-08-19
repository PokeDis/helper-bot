from custom_durations.constants import *
from custom_durations.exceptions import InvalidTokenError, ScaleFormatError
from custom_durations.scales import Scale


def valid_token(token):
    is_scale = False

    try:
        Scale(token)
        is_scale = True
    except ScaleFormatError:
        pass

    if any([token.isdigit(), token in SEPARATOR_TOKENS, is_scale]):
        return True

    return False


def compute_char_token(c):
    if c.isdigit():
        return SCALE_TOKEN_DIGIT
    elif c.isalpha():
        return SCALE_TOKEN_ALPHA

    return None


def extract_tokens(representation, separators=SEPARATOR_CHARACTERS):
    buff = ""
    elements = []
    last_token = None

    for index, c in enumerate(representation):
        if c in separators:
            if buff:
                if not valid_token(buff):
                    raise InvalidTokenError(
                        "Duration representation {0} contains "
                        "an invalid token: {1}".format(representation, buff)
                    )

                if not buff.strip() in SEPARATOR_TOKENS:
                    elements.append(buff)

            buff = ""
            last_token = None
        else:
            token = compute_char_token(c)
            if token is not None and last_token is not None and token != last_token:
                elements.append(buff)
                buff = c
            else:
                buff += c

            last_token = token

    elements.append(buff)

    return list(zip(elements[::2], elements[1::2]))
