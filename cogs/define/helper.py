from urllib.parse import quote_plus

from PyDictionary import PyDictionary
from udpy import UrbanClient

from utils.regexp import get_words_between_brackets  # pylint: disable=import-error

dictionary = PyDictionary()
urban = UrbanClient()


def dictionary_define(word):
    definition = dictionary.meaning(word)
    if definition is None:
        return None
    else:
        synonym = dictionary.synonym(word)
        antonym = dictionary.antonym(word)

        return {
            "definition": definition,
            "synonym": synonym if synonym is not None else [f"No synonyms for {word}."],
            "antonym": antonym if antonym is not None else [f"No antonyms for {word}."],
        }


base_url = r"https://www.urbandictionary.com/define.php?term="


def urban_define(word):
    urban_word = urban.get_definition(word)
    if len(urban_word) == 0:
        return None
    else:
        urban_word = urban_word[0]
        linked_definition = urban_word.definition
        links = get_words_between_brackets(urban_word.definition)
        for link in links:
            linked_definition = linked_definition.replace(
                link,
                f'{link}({base_url}{quote_plus(link.translate({ord(c): None for c in "[]"}))})',
            )
    return {
        "word": urban_word.word,
        "definition": linked_definition,
        "example": urban_word.example,
    }