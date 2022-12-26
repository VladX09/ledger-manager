from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.theme import Theme


class CustomHighlighter(RegexHighlighter):
    base_style = "custom."
    highlights = [
        r"(?P<date>\d{4}/\d{2}/\d{2}\s\d{2}:\d{2}:\d{2})",
        r"(?P<date>\d{4}/\d{2}/\d{2})",
        r"(?P<date>\d{4}-\d{2}-\d{2})",
        r"(?P<date>\d{2}-\w{3}-\d{2})",
        r"(?P<price>\-?\d+((\.|\,)\d*)+)",
        r"(?P<commodity>(\b(?!MIR|VISA)[A-Z]{2,}|\$+|\€+|\₽+))",
        r"(?P<unimportant>(\<None\>)|(\<Total\>)|(\s0\s))",
        r"(?P<account>\:?[A-Z][a-z]+([A-Z][a-z]*)*(\:[A-Z][a-z]+([A-Z][a-z]*)*)*|:?MIR|:?VISA)",
    ]


theme = Theme({
    "custom.date": "magenta",
    "custom.price": "deep_sky_blue2",
    "custom.commodity": "cyan",
    "custom.unimportant": "grey69",
    "custom.account": "bold",
})

console = Console(highlighter=CustomHighlighter(), theme=theme)

__all__ = ["console"]
