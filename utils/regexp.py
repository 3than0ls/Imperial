import re

pattern = re.compile(r"(?<!^)(?=[A-Z])")


def pascal_to_words(pascalCaseString):
    # "words" just means they have spaces between words
    return pattern.sub(" ", pascalCaseString)


def word_to_pascal(wordsString):
    return "".join(wordsString.title().split(" "))
