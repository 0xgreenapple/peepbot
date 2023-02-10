import asyncio
from collections import UserDict


class Max_item_reached(Exception):
    def __str__(self):
        return f'maximum number of values has been reached'


class cache(UserDict):
    """ subclass of dict object """

    def __init__(self, max_value: int = 2000):
        super().__init__()
        self.__max_size = max_value
        self.__recentValue = None

    def __setitem__(self, key, value):
        if len(self.items()) > self.__max_size:
            raise Max_item_reached()
        self.recentValue = {key: value}
        return super().__setitem__(key, value)

    @property
    def GetRecent(self):
        return self.__recentValue

    @property
    def GetMaxSize(self):
        return self.__max_size

    def Insert(self, key, value=None):
        return self.__setitem__(key=key, value=value)

    def Delete(self, key):
        return self.__delitem__(key=key)

    def CleanUp(self):
        for key in self.items():
            self.__delitem__(key)





