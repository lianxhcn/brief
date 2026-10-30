"""Width-aware mixed Chinese/Latin wrapping without a graphics dependency."""
import re

TOKENS = re.compile(r'install\.packages\([^\n)]*\)|pip install [A-Za-z0-9_.-]+|[A-Za-z0-9_]+(?:[.\-/\u2019\u0027][A-Za-z0-9_]+)*|.', re.DOTALL)
CLOSING = set('，。！？、；：）】》〕〉”’」』.,!?;:%)]}…')
OPENING = set('（【《〔〈“‘「『([{')


def wrap_text(value, font, width):
    if width <= 0:
        raise ValueError('Width must be positive')
    lines = []
    for paragraph in value.split('\n'):
        current = []
        tokens = []
        for atom in TOKENS.findall(paragraph):
            # An overlong URL or identifier cannot remain atomic.
            tokens.extend(list(atom) if font.getlength(atom) > width else [atom])
        for token in tokens:
            if current and font.getlength(''.join(current) + token) > width:
                carry = []
                if token in CLOSING:
                    while current and not current[-1].strip():
                        current.pop()
                    if current:
                        last = current.pop()
                        if font.getlength(last + token) > width and len(last) > 1:
                            current.append(last[:-1])
                            last = last[-1:]
                        carry.insert(0, last)
                while current and current[-1] in OPENING:
                    carry.insert(0, current.pop())
                if current:
                    lines.append(''.join(current).rstrip())
                current = carry
            if not current and token.isspace():
                continue
            current.append(token)
        lines.append(''.join(current).rstrip())
    return lines
