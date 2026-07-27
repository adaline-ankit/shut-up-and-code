def get_user_by_id(user_id):
    """
    Gets a user by id.

    This function takes a user id and returns the user.
    """
    return db.get(user_id)


def parse_config(path):
    """Parse the config at path.

    Args:
        path: The path to parse.
    Returns:
        The parsed config.
    """
    return {}
