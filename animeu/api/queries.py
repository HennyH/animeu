# /animeu/api/queries.py
#
# Query functions for the API.
#
# See /LICENCE.md for Copyright information
"""Query functions for the API."""
from itertools import chain
import regex as re
from animeu.data_loader import load_character_data

def query_characters(name=None, anime=None, tags=None, description=None):
    """Find all characters matching some set of filters."""
    tags = tags or []

    def compile_or_escape_re(maybe_pattern):
        """Try compile a string as a regex otherwise escape the string."""
        if maybe_pattern is None:
            return None
        try:
            return re.compile(maybe_pattern, flags=re.IGNORECASE)
        except re.error:
            return re.compile(re.escape(maybe_pattern))

    name_re = compile_or_escape_re(name)
    anime_re = compile_or_escape_re(anime)
    tag_res = [compile_or_escape_re(t) for t in tags]
    description_re = compile_or_escape_re(description)
    for character in load_character_data():
        character_names = list(chain.from_iterable(character["names"].values()))
        if name_re and not \
                any(name_re.search(n, timeout=0.5) for n in character_names):
            continue
        character_animes = (role["name"] for role in character["anime_roles"])
        if anime_re and not \
                any(anime_re.search(a, timeout=0.5) for a in character_animes):
            continue
        character_tags = character["tags"]
        if tag_res and not \
                all(any(r.search(t) for t in character_tags) for r in tag_res):
            continue
        character_descriptions = character["descriptions"]
        if description_re and not \
                any(description_re.search(d) for d in character_descriptions):
            continue
        yield character

# pylint: disable=too-many-arguments
def paginate_query_characters(page=0,
                              limit=100,
                              name=None,
                              anime=None,
                              tags=None,
                              description=None):
    """Return a paginated view of the characters."""
    if name is None and anime is None and tags is None and description is None:
        characters = load_character_data()
    else:
        characters = list(query_characters(name=name,
                                           anime=anime,
                                           tags=tags,
                                           description=description))
    start_index = page * limit
    end_index = start_index + limit
    page_of_characters = characters[start_index:end_index]
    return {
        "characters": page_of_characters,
        "count": len(page_of_characters),
        "total": len(characters)
    }
