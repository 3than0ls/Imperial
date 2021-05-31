from urllib.parse import quote_plus

from PyDictionary import PyDictionary
from udpy import UrbanClient

from utils.regexp import get_words_between_brackets  # pylint: disable=import-error

dictionary = PyDictionary()
urban = UrbanClient()

dict_cache = {}  # maybe improve cache by moving it to back end


def dictionary_define(word):
    if word in dict_cache:
        return dict_cache[word]

    definition = dictionary.meaning(word)
    if definition is None:
        return None
    else:
        synonym = dictionary.synonym(word)
        antonym = dictionary.antonym(word)

        data = {
            "definition": definition,
            "synonyms": synonym
            if synonym is not None
            else [f"No synonyms for {word}."],
            "antonyms": antonym
            if antonym is not None
            else [f"No antonyms for {word}."],
        }
        dict_cache[word] = data
        return data


base_url = r"https://www.urbandictionary.com/define.php?term="


def apply_links(text):
    links = get_words_between_brackets(text)
    linked = text
    for link in links:
        linked = linked.replace(
            link,
            f'{link}({base_url}{quote_plus(link.translate({ord(c): None for c in "[]"}))})',
        )
    return linked


urban_cache = {}


def urban_define(word):
    if word in urban_cache:
        return urban_cache[word]

    urban_word = urban.get_definition(word)
    if len(urban_word) == 0:
        return None
    else:
        urban_word = urban_word[0]

    data = {
        "word": urban_word.word,
        "definition": apply_links(urban_word.definition),
        "example": apply_links(urban_word.example),
    }
    urban_cache[word] = data
    return data
