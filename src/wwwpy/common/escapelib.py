# Create a translation table for the specified characters
escape_table = str.maketrans({
    '\r': '\\r',  # Carriage return -> \r
    '\n': '\\n',  # Newline (line feed) -> \n
    '\t': '\\t',  # Tab -> \t
    '\\': '\\\\'  # Backslash -> \\
})


def escape_string(s: str) -> str:
    return s.translate(escape_table)


def unescape_string(s: str) -> str:
    escaped_bytes = s.encode('ascii', 'backslashreplace')
    return escaped_bytes.decode('unicode_escape')
