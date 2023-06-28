
from typing import List, Any
import abc

class Emitter(metaclass=abc.ABCMeta):
    """
    Abstract class for all emitter classes.
    """

    @abc.abstractmethod
    async def aemit(self, events:List[Any]=None):
        """
        Method that actually does the work.
        """
