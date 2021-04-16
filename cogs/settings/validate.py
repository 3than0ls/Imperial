from firecord import DEFAULT_CONFIG  # pylint: disable=import-error


# the validation functions below have to define constraints of the only parameter value provided
def _prefix(value):
    # for convenience, limit prefix size to greater than 0 and less than or equal to 5
    return len(value) > 0 and len(value) <= 5


def _security(value):
    # same as writing value == "none" or value == ...
    return value in ["none", "server_manager", "admin", "owner"]


validation_rules = {
    setting_name: globals()[f"_{setting_name}"]
    for setting_name in DEFAULT_CONFIG.keys()
    if f"_{setting_name}" in globals()
}
