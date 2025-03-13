from dataclasses import dataclass
from typing import Union, List

@dataclass
class ErrorsModel():
    error_id: Union[int, List[int]]
    error_message: Union[str, List[str]]
    multiple_errors: bool