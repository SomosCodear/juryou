import abc
from typing import List
from juryou import receipt


class BaseBackend(abc.ABC):
    @abc.abstractmethod
    def commit(self, receipt: 'receipt.Receipt') -> 'receipt.Receipt':
        """ Commit the given receipt to the backend.

        This will impact the receipt details on the backend, making it a "valid" receipt and ready
        to be printed.
        """
        pass

    @abc.abstractclassmethod
    def fetch(self, identifier: str) -> 'receipt.Receipt':
        """ Fetch a receipt by the identifier used by the backend. """
        pass

    @abc.abstractclassmethod
    def fetch_last(self, identifier: str, count: int = 1) -> List['receipt.Receipt']:
        """ Fetch the last receipt commited to the backend.
        Optionally, provide a count to indicate the amount of last receipts to fetch.
        """
        pass
