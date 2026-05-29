import re


def normalize_title(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9\s]", "", title)  # strip all non-alphanumeric (incl. underscores)
    title = re.sub(r"\s+", "_", title.strip())
    return title
