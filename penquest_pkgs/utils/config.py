import configparser
from typing import Union, Type

def retrieve_value_from_config(
        config: configparser.ConfigParser, 
        super_field: str, 
        sub_field:str, 
        d_type: Type,
        field_name: str,
        parameter: Union[str, int] = None
    ) -> Union[str, int]:
    """Checks if the parameter is None and if so tries to load a default value
    from the default config. If a parameter is supplied, then parameter value
    is preferred over default config.

    :param config: config file that stores the default configs
    :param super_field: super field within the default config
    :param sub_field: sub field within the default config
    :param d_type: data type of the stored field in the config
    :param field_name: name of the field that is tried to retrieved
    :param parameter: paramter which may overwrite the default config value, 
        defaults to None
    :raises RuntimeError: paramter is None and there is no value in the defualt
        config
    :return: parameter value or default config value
    """
    if parameter is not None:
        return parameter
    if super_field in config and sub_field in config[super_field]:
        return d_type(config[super_field][sub_field])
    else:
        raise RuntimeError(f"No {field_name} specified")