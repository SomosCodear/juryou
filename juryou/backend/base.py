import abc
from juryou import receipt


class BaseBackend(abc.ABC):
    @abc.abstractmethod
    def commit(self, receipt: 'receipt.Receipt') -> 'receipt.Receipt':
        pass
