from firecord import DEFAULT_CONFIG  # pylint: disable=import-error


# the validation functions below have to define constraints of the only parameter value provided
def _prefix(value):
    # for convenience, limit prefix size to greater than 0 and less than or equal to 5
    return len(value) > 0 and len(value) <= 5


def _nickname(value):
    # discord nicknames must be greater than zero but less or equal to 32
    return len(value) > 0 and len(value) <= 32


def _security(value):
    # same as writing value == "none" or value == ...
    return value in ["none", "server_manager", "admin", "owner"]


validation_rules = {
    setting_name: (
        globals()[f"_{setting_name}"]
        if f"_{setting_name}" in globals()
        else lambda: False  # default is unable to change, so be sure to include a validation option
    )
    for setting_name in DEFAULT_CONFIG.keys()
}
