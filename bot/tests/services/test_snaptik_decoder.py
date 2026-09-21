import pytest

from services.tiktok.extractor.snaptik._decoder import decoder


@pytest.mark.parametrize(
    ("encoded_text", "alphabet", "offset", "radix", "expected"),
    [
        ("gf|gg|", "abcdefghij|", 0, 10, "AB"),
        ("41|42|", "0123456789abcdef|", 0, 16, "AB"),
        ("hg|hh|", "abcdefghij|", 11, 10, "AB"),
        ("", "abcdefghij|", 0, 10, ""),
    ],
)
def test_decoder(
    encoded_text: str, alphabet: str, offset: int, radix: int, expected: str
) -> None:
    assert decoder(encoded_text, "", alphabet, offset, radix, "") == expected


@pytest.mark.parametrize("encoded_text", ["gf", "z|", "|"])
def test_decoder_rejects_invalid_encoding(encoded_text: str) -> None:
    with pytest.raises(ValueError):
        decoder(encoded_text, "", "abcdefghij|", 0, 10, "")
