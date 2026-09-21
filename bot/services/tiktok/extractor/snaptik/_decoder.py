_RADIX_DIGITS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/"


def _decode_number(encoded_number: str, source_radix: int) -> int:
    """Read a Snaptik number using the digits in its source radix."""
    if not 2 <= source_radix <= len(_RADIX_DIGITS):
        raise ValueError("Invalid Snaptik source radix")
    if not encoded_number:
        raise ValueError("Empty Snaptik number")

    digit_symbols = _RADIX_DIGITS[:source_radix]
    value = 0
    for symbol in encoded_number:
        try:
            digit = digit_symbols.index(symbol)
        except ValueError as error:
            raise ValueError(f"Invalid Snaptik digit: {symbol!r}") from error
        value = value * source_radix + digit

    if value == 0:
        raise ValueError("Zero is not a Snaptik character code")
    return value


def decoder(
    encoded_text: str,
    _unused_second_argument: str,
    alphabet: str,
    codepoint_offset: int,
    source_radix: int,
    _unused_sixth_argument: str,
) -> str:
    """Decode the six-value Snaptik response into HTML containing media links.

    The alphabet maps symbols to decimal digits. Its character at source_radix
    separates encoded Unicode code points; codepoint_offset is subtracted from
    each decoded number. The second and sixth response values are unused.
    """
    if not encoded_text:
        return ""
    try:
        separator = alphabet[source_radix]
    except IndexError as error:
        raise ValueError("Snaptik alphabet has no separator") from error
    if not encoded_text.endswith(separator):
        raise ValueError("Snaptik text has no final separator")

    characters = []
    for encoded_character in encoded_text.split(separator)[:-1]:
        decimal_digits = encoded_character
        for digit, symbol in enumerate(alphabet):
            decimal_digits = decimal_digits.replace(symbol, str(digit))
        codepoint = _decode_number(decimal_digits, source_radix)
        characters.append(chr(codepoint - codepoint_offset))
    return "".join(characters)
