from firecord import DEFAULT_CONFIG  # pylint: disable=import-error


def _prefix(value):
    return not (len(value) > 0 and len(value) <= 5)


validation_rules = {
    setting_name: (globals()[f"_{setting_name}"] if setting_name in globals() else True)
    for setting_name in DEFAULT_CONFIG.keys()
}
