#!/usr/bin/env python3
import re
from urllib.parse import urlparse

TOKEN = re.compile(r"(\*\*[^*]+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))")
LINK = re.compile(r"^\[([^\]]+)\]\(([^)]+)\)$")


def plain_inline(text):
    value = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"\*\*([^*]+?)\*\*", r"\1", value)
    return value.replace("**", "")


def tex_url(url):
    return url.replace("\\", "/").replace("%", r"\%").replace("&", r"\&").replace("_", r"\_").replace("#", r"\#")


def tex_inline(codec, text):
    output = []
    position = 0
    for match in TOKEN.finditer(text):
        output.append(codec.tex(text[position:match.start()].replace("**", "")))
        token = match.group(0)
        if token.startswith("**"):
            output.append(r"\textbf{" + tex_inline(codec, token[2:-2]) + "}")
        elif token.startswith("`"):
            output.append(r"\texttt{" + codec.tex(token[1:-1]) + "}")
        else:
            label, url = LINK.match(token).groups()
            if urlparse(url).scheme in {"http", "https"}:
                output.append(r"\href{" + tex_url(url) + "}{" + tex_inline(codec, label) + "}")
            else:
                output.append(tex_inline(codec, label))
        position = match.end()
    output.append(codec.tex(text[position:].replace("**", "")))
    return "".join(output).replace(r"\textbackslash{}\textbackslash{}", "")
