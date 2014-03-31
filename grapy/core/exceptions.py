__all__ = ['EngineError', 'DropItem', 'IgnoreRequest', 'RetryRequest', 'ItemError']

class EngineError(Exception):
    pass

class DropItem(Exception):
    pass

class IgnoreRequest(Exception):
    pass

class RetryRequest(Exception):
    pass

class ItemError(Exception):
    pass
