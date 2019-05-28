"""
Patches bugs in ruamel.yaml unless or until they are patched in the ruamel.yaml
package itself.

Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any
from ruamel.yaml.emitter import (
    Emitter,
    EmitterError,
)


# Stop Emitter.write_folded from injecting unnecessary new-lines
def write_folded_fix(self, text):
    # type: (Emitter, Any) -> None
    hints, _indent, _indicator = self.determine_block_hints(text)
    self.write_indicator(u'>' + hints, True)
    if _indicator == u'+':
        self.open_ended = True
    self.write_line_break()
    leading_space = True
    spaces = False
    breaks = True
    start = end = 0
    while end <= len(text):
        ch = None
        if end < len(text):
            ch = text[end]
        if breaks:
            if ch is None or ch not in u'\n\x85\u2028\u2029\a':
                if (
                    not leading_space
                    and ch is not None
                    and ch != u' '
                    and text[start] == u'\n'
                ):
                    self.write_line_break()
                leading_space = ch == u' '

                # This must apply only to the very last character
                if end == len(text):
                    for br in text[start:end]:
                        if br == u'\n':
                            self.write_line_break()
                        else:
                            self.write_line_break(br)

                if ch is not None:
                    self.write_indent()
                start = end
        elif spaces:
            if ch != u' ':
                if start + 1 == end and self.column > self.best_width:
                    self.write_indent()
                else:
                    data = text[start:end]
                    self.column += len(data)
                    if bool(self.encoding):
                        data = data.encode(self.encoding)
                    self.stream.write(data)
                start = end
        else:
            if ch is None or ch in u' \n\x85\u2028\u2029\a':
                data = text[start:end]
                self.column += len(data)
                if bool(self.encoding):
                    data = data.encode(self.encoding)
                self.stream.write(data)
                if ch == u'\a':
                    if end < (len(text) - 1) and not text[end + 2].isspace():
                        self.write_line_break()
                        self.write_indent()
                        # \a and the space that is inserted on the fold
                        end += 2
                    else:
                        raise EmitterError(
                            'unexcpected fold indicator \\a before space'
                        )
                if ch is None:
                    self.write_line_break()
                start = end
        if ch is not None:
            breaks = ch in u'\n\x85\u2028\u2029'
            spaces = ch == u' '
        end += 1


Emitter.write_folded = write_folded_fix
