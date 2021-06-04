def proper(list):
    """turns a list of items into a string, but it has the "and" at the end, meaning we can't just use .join()"""
    string = ""

    for i, item in enumerate(list):
        item = str(item)
        if i == 0:
            string += item
        elif i != len(list) - 1:
            string += f", {item}"
        elif i == len(list) - 1:
            string += f", and {item}"

    if len(list) == 2:  # if there's only 2 items, there doesn't need to be a comma
        string = string.replace(",", "")

    return string
