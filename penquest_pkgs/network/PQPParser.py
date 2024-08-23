from typing import Dict, List, Type, Optional, TypeVar, ForwardRef, Any
from penquest_pkgs.network.ProtocolParts import Required, Optional, Options
from penquest_pkgs.network.game_messages import inbound as InboundMessages
from penquest_pkgs.network.game_messages import message_models as MessageModels
from penquest_pkgs.utils.logging import get_logger
from collections.abc import Iterable

T = TypeVar('T')

class PQPParser():
    """PenQuest Protocol Parser
    Parses incoming messages from the gateway into a corresponding message 
    object. 
    """

    def __init__(self):
        pass

    def try_parse_message(self, message:Any, dtypes: List[Type]):
        """Tries to parse the message into one of the types provided. The first 
        type that fits is selected. In case no type fits, 

        Args:
            message (Dict): the message to be parsed
            dtypes (List[Type]): a list of possible types the message should be
            parsed to

        Returns:
            Optional[None, T]: either an object of the first type that fits the
            message or None
        """
        if isinstance(message, list):
            for dtype in dtypes:
                if dtype.__name__ != "List":
                    continue
                parsed_message = []
                for elem in message:
                    parsed_elem = self.try_parse_message(elem, [dtype.__args__[0]])
                    if parsed_elem is None:
                        break
                    else:
                        parsed_message.append(parsed_elem)
                if len(parsed_message) == len(message):
                    return parsed_message
            return None
        elif isinstance(message, dict):
            if isinstance(dtypes, Iterable):
                for dtype in dtypes:
                    relevant_field_names = [
                        field_name 
                        for field_name, requirement in dtype.__dict__.items() 
                        if not field_name.startswith("__") and isinstance(requirement, Required)
                    ]
                    if len(relevant_field_names) > 0 and all([field_name in message for field_name in relevant_field_names]):
                        return self.parse_message(message, dtype)
        else:
            for dtype in dtypes:
                obj = None
                try:
                    obj = dtype(message)
                except Exception:
                    pass
                if obj is not None:
                    return obj

        return None
    
    def dynamic_type_loading(self, type_name: str) -> Type:
        """ Loads python class based on a name string from a package during
        runtime.

        Args:
            type_name (str): _description_

        Returns:
            Type: _description_
        """
        packages = [InboundMessages, MessageModels]
        for package in packages:
            for dtype in package.__dict__:
                if not dtype.startswith("__"):
                    if dtype == type_name:
                        return getattr(package, dtype)
        
        raise ValueError(f"Type '{type_name} not found")
    
    def _parse_list(self, l: List, dtype: Type) -> List:
        if isinstance(dtype, ForwardRef):
            dtype = self.dynamic_type_loading(
                dtype.__forward_arg__
            )
        new_list = []
        for elem in l:
            if type(elem) == dict:
                new_elem = self.parse_message(elem, dtype)
            else:
                new_elem = dtype(elem)
            new_list.append(new_elem)
        return new_list


    def parse_message(self, message:Dict, dtype:Type) -> T:
        """Parses 

        Args:
            message (Dict): _description_
            dtype (Type): _description_

        Raises:
            ValueError: missing required field
            ValueError: value is None
            ValueError: cannot be parsed to the provided types
            ValueError: field does not contain a list, although it should
            ValueError: no type provided
            ValueError: not a dictionary

        Returns:
            T: object of the provided type
        """
        obj = dtype()
        

        for field_name, field_type in dtype.__dict__.items():
            if not field_name.startswith("__"):
                get_logger(__name__).log(5, f"parsing field '{field_name}' to designated type '{field_type.dtype}'")
                # Raise error for fields that are required in a message but not
                # present; missing optional fields are set to None
                if isinstance(field_type.dtype, ForwardRef):
                    field_type.dtype = self.dynamic_type_loading(
                        field_type.dtype.__forward_arg__
                    )
                
                if field_name not in message:
                    if isinstance(field_type, Required):
                        raise ValueError(
                            f"Message does not contain required field "
                            f"'{field_name}'"
                        )
                    if isinstance(field_type, Optional):
                        setattr(obj, field_name, None)
                    continue

                # handle fields that have None as value
                message_value = message[field_name]
                if message_value is None:
                    if not field_type.nullable:
                        raise ValueError(
                            f"Field '{field_name}' is None (if this should "
                            "be allowed set nullable=True)"
                        )
                else:
                    if isinstance(field_type.dtype, Options):
                        message_obj = self.try_parse_message(
                            message_value, 
                            field_type.dtype.dtypes
                        )
                        if message_obj is None:
                             if not field_type.nullable:
                                raise ValueError(
                                    f"Field '{field_name}' could not be parsed "
                                    "to any of the provided types"
                                )
                        message_value = message_obj
                    # handle fields which's value is a list
                    # CAUTION: dictionaries only have a field __name__ since
                    # python 3.10
                    elif field_type.dtype.__name__ == "List": 
                        if type(message_value) != list:
                            raise ValueError(
                                f"Field '{field_name}' is not a list"
                            )
                        if len(field_type.dtype.__args__) == 0:
                            raise ValueError(
                                f"No type for list field '{field_name}' provided"
                            )
                        target_dtype = field_type.dtype.__args__[0]
                        message_value = self._parse_list(message_value, target_dtype)
                    # handle fields which's value is a dict
                    elif field_type.dtype.__name__ == "Dict":
                        if type(message_value) != dict:
                            raise ValueError(
                                f"Field '{field_name}' is not a dict"
                            )
                        if len(field_type.dtype.__args__) != 2:
                            raise ValueError(
                                f"No types for dict field '{field_name}' provided"
                            )
                        key_type = field_type.dtype.__args__[0]
                        value_type = field_type.dtype.__args__[1]
                        get_logger(__name__).log(5, f"key_type '{key_type}' value_type '{value_type}'")
                        new_dict = dict()
                        for key, value in message_value.items():
                            if value is None:
                                continue
                            parsed_key = key_type(key)
                            if type(value) == dict:
                                parsed_value = self.parse_message(value, value_type)
                            elif type(value) == list:
                                target_dtype = field_type.dtype.__args__[0]
                                parsed_value = self._parse_list(value, target_dtype)
                            else:
                                parsed_value = value_type(value)
                            new_dict[parsed_key] = parsed_value
                        message_value = new_dict
                    # handle fields which's value is a custom type
                    elif field_type.dtype.__name__ in MessageModels.__dict__:
                        if type(message_value) != dict:
                            message_value = field_type.dtype(message_value)
                            #raise ValueError(f"Field '{field_name}' is not a dictionary")
                        else:
                            message_value = self.parse_message(
                                message_value, 
                                field_type.dtype
                            )
                    else:
                        # handle base types and cast value of the field into the
                        # correct data type
                        message_value = field_type.dtype(message_value)
                # set value of the object attribute with the corresponding field
                # name
                setattr(obj, field_name, message_value)
        get_logger(__name__).log(5, f"parsed object: {obj.__dict__}")
        return obj