"""
Aider-style SEARCH/REPLACE diff utilities.

Format:
<<<<<<< SEARCH
exact text to find
=======
replacement text
>>>>>>> REPLACE
"""

import re


class DiffError(Exception):
    """Raised when SEARCH block doesn't match."""
    pass


def apply_search_replace(content: str, original: str) -> str:
    """
    Apply Aider-style SEARCH/REPLACE blocks to original content.

    Args:
        content: Text containing SEARCH/REPLACE blocks (or full file content)
        original: Existing file content to modify

    Returns:
        Modified content

    Raises:
        DiffError: If any SEARCH block not found in original
    """
    pattern = r'<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE'
    blocks = list(re.finditer(pattern, content, re.DOTALL))

    if not blocks:
        return content  # No diff blocks, treat as full content

    result = original

    for block in blocks:
        search_text = block.group(1)
        replace_text = block.group(2)

        # Exact match
        if search_text in result:
            result = result.replace(search_text, replace_text, 1)
            continue

        # Fuzzy: normalize whitespace
        if _fuzzy_replace(result, search_text, replace_text) is not None:
            result = _fuzzy_replace(result, search_text, replace_text)
            continue

        raise DiffError(f"SEARCH block not found:\n{search_text[:100]}...")

    return result


def _fuzzy_replace(text: str, search: str, replace: str) -> str | None:
    """Try whitespace-normalized matching. Returns None if no match."""
    def normalize(s: str) -> str:
        return re.sub(r'[ \t]+', ' ', s.strip())

    search_lines = search.strip().split('\n')
    text_lines = text.split('\n')

    # Single line
    if len(search_lines) == 1:
        search_norm = normalize(search)
        for i, line in enumerate(text_lines):
            if normalize(line) == search_norm:
                text_lines[i] = replace
                return '\n'.join(text_lines)
        return None

    # Multi-line
    search_norm = [normalize(l) for l in search_lines]
    for i in range(len(text_lines) - len(search_lines) + 1):
        chunk_norm = [normalize(l) for l in text_lines[i:i + len(search_lines)]]
        if chunk_norm == search_norm:
            text_lines[i:i + len(search_lines)] = replace.split('\n')
            return '\n'.join(text_lines)

    return None
