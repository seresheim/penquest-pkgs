from typing import Type, List


class Required():

    def __init__(self, dtype:Type, nullable:bool=False):
        self.dtype = dtype
        self.nullable = nullable


class Optional():

    def __init__(self, dtype: Type, nullable:bool=False):
        self.dtype = dtype
        self.nullable = nullable

class Options():

    def __init__(self, dtypes: List[Type]):
        self.dtypes = dtypes