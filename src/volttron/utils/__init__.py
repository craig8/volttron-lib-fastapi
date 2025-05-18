from copy import deepcopy


def load_config(default_configuration: str | Path | dict | None) -> dict:
    """
    Load the default configuration from a JSON or YAML encoded file.

    If default_configuration is None then return {}.

    If default_configuration is a dictionary, then return a deep copy of the dictionary
    without any changes to it.

    If default_configuration is a string or Path object, they must resolve to a file that
    is readable by the current process.  The file referenced will be parsed and loaded
    using yaml.safe_load.  Doing so will load both json or yaml based files.

    :param default_configuration: An agent configuration that is passed to __init__
    :type default_configuration: str | Path | dict
    :raises ValueError: If default_configuration is not resolvable.
    :return: A dictionary of the parsed default_configuration.
    :rtype: dict
    """

    if default_configuration is None or default_configuration == "":
        return {}

    if isinstance(default_configuration, dict):
        return deepcopy(default_configuration)

    if isinstance(default_configuration, str):
        default_configuration = Path(default_configuration).expanduser().absolute()
    elif isinstance(default_configuration, Path):
        default_configuration = default_configuration.expanduser().absolute()
    else:
        ValueError(
            f"Invalid type passed as default_configuration {type(default_configuration)} MUST be str | Path | dict | None"
        )

    # First attempt parsing the file with a yaml parser (allows comments natively)
    # Then if that fails we fallback to our modified json parser.
    try:
        return yaml.safe_load(default_configuration.read_text())
    except yaml.YAMLError as e:
        try:
            return parse_json_config(default_configuration.read_text())
        except Exception as e:
            _log.error("Problem parsing agent configuration")
            raise