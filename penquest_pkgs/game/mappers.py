import penquest_pkgs.network.game_messages.message_models as mm
import penquest_pkgs.model as m


def map_message2model(mm_obj):
    """Maps the objects of the network layer (inbound messages as well as
    message model objects) into objects of the regulary model.
    """
    
    if isinstance(mm_obj, list):
        return [map_message2model(item) for item in mm_obj]
    if isinstance(mm_obj, dict):
        return {
            key: map_message2model(value) 
            for key, value in mm_obj.items()
        }
    if mm_obj.__class__.__name__ not in m.__dict__:
        #raise ValueError(
        #    f"Class {mm_obj.__class__.__name__} not found in 
        #    models.py"
        #)
        return mm_obj

    model_class = m.__dict__[mm_obj.__class__.__name__]
    kwargs = {}
    for field_name, field_obj in model_class.__dataclass_fields__.items():
        if hasattr(mm_obj, field_name) and not field_name.startswith("__"):
            attribute = getattr(mm_obj, field_name)
            if isinstance(attribute, list):
                kwargs[field_name] = [
                    map_message2model(item) for item in attribute
                ]
            elif isinstance(attribute, dict):
                kwargs[field_name] = {
                    key: map_message2model(value) 
                    for key, value in attribute.items()
                }
            elif attribute.__class__.__name__ in m.__dict__:
                kwargs[field_name] = map_message2model(attribute)
            else:
                kwargs[field_name] = attribute
    model_obj = model_class(**kwargs)
    return model_obj

def map_model2message(m_obj):
    """Maps the objects of the model to message models of the network layer

    :param m_obj: _description_
    """
    
    if isinstance(m_obj, list):
        return [map_model2message(item) for item in m_obj]
    if isinstance(m_obj, dict):
        return {
            key: map_model2message(value) 
            for key, value in m_obj.items()
        }
    if m_obj.__class__.__name__ not in mm.__dict__:
        #raise ValueError(
        #    f"Class {m_obj.__class__.__name__}
        #    not found in message_models.py"
        #)
        return m_obj

    message_model_class = mm.__dict__[m_obj.__class__.__name__]
    kwargs = {}
    for field_name, field_obj in message_model_class.__dataclass_fields__.items():
        if hasattr(m_obj, field_name) and not field_name.startswith("__"):
            attribute = getattr(m_obj, field_name)
            if isinstance(attribute, list):
                kwargs[field_name] = [
                    map_model2message(item) for item in attribute
                ]
            elif isinstance(attribute, dict):
                kwargs[field_name] = {
                    key: map_model2message(value) 
                    for key, value in attribute.items()
                }
            elif attribute.__class__.__name__ in mm.__dict__:
                kwargs[field_name] = map_model2message(attribute)
            else:
                kwargs[field_name] = attribute
    message_model_obj = message_model_class(**kwargs)
    return message_model_obj 