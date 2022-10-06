import discord


class EconomyException(Exception):
    """
    Main exception class for economy related errors
    """
    pass


class UserHasNotEnoughCoins(EconomyException):
    def __init__(self, message: str = " user already has no coins"):
        self.message = message
        super().__init__(message)


class NotEnoughMembers(EconomyException):
    def __init__(self, message: str = " this guild has no enough members"):
        self.message = message
        super().__init__(message)


class DataDoesNotExists(EconomyException):
    def __init__(self,Member:discord.Member = None, message: str = " the data for this user does not exists"):
        self.Member = Member
        self.message = f" the data for {self.Member} doesnt exists" if self.Member else message
        super().__init__(self.message)

class NotFound(EconomyException):
    def __init__(self, data: str = None, message: str = "the data does not exist"):
        self.data = data
        self.message = f" {self.data} doesnt exists in the database " if data else message
        super().__init__(self.message)


class ItemNotFound(EconomyException):
    def __init__(self, data: str = None, message: str = "the item that you were looking for does not exists"):
        self.data = data
        self.message = f" {self.data} doesnt exists in the database " if data else message
        super().__init__(self.message)


class BadRequest(EconomyException):
    def __init__(self, message: str = "there is something wrong about your request"):
        self.message = message
        super().__init__(self.message)

