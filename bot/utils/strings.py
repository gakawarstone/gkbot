import unicodedata


def remove_emoji(text: str) -> str:
    def iter_graphemes(s):
        i = 0
        n = len(s)
        while i < n:
            cluster = s[i]
            i += 1
            # collect following marks (category starts with 'M')
            while i < n and unicodedata.category(s[i]).startswith("M"):
                cluster += s[i]
                i += 1
            # include ZWJ sequences (emoji like 👩‍👩‍👧‍👧)
            while i < n and ord(s[i]) == 0x200D:
                cluster += s[i]
                i += 1
                if i < n:
                    cluster += s[i]
                    i += 1
                    while i < n and unicodedata.category(s[i]).startswith("M"):
                        cluster += s[i]
                        i += 1
            yield cluster

    def is_emoji_codepoint(cp):
        # cp is an integer code point
        return (
            0x1F600 <= cp <= 0x1F64F  # emoticons
            or 0x1F300 <= cp <= 0x1F5FF  # symbols & pictographs
            or 0x1F680 <= cp <= 0x1F6FF  # transport & map
            or 0x1F1E6 <= cp <= 0x1F1FF  # regional indicators (flags)
            or 0x2600 <= cp <= 0x26FF  # misc symbols
            or 0x2700 <= cp <= 0x27BF  # dingbats
            or 0xFE00 <= cp <= 0xFE0F  # variation selectors (FE0E/FE0F)
            or 0x1F900 <= cp <= 0x1F9FF  # supplemental symbols
            or 0x1FA70 <= cp <= 0x1FAFF  # extended-A
            or 0x1F700 <= cp <= 0x1F77F
            or 0x1F780 <= cp <= 0x1F7FF
            or 0x1F3FB <= cp <= 0x1F3FF  # skin tone modifiers
            or cp == 0x200D  # ZWJ
        )

    out = []
    for g in iter_graphemes(text):
        if any(is_emoji_codepoint(ord(ch)) for ch in g):
            # drop the whole grapheme cluster
            continue
        out.append(g)
    return "".join(out)
