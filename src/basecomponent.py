from abc import abstractclassmethod

class Promps(object):
    _promps_dict : dict

    def __init__(self, **promps) -> None:
        self._promps_dict = promps

    def __getattr__(self, __name: str) -> any:
        if __name in self._promps_dict:
            return self._promps_dict[__name]
        else:
            return self.__getattribute__(__name)

    def __getitem__(self, key):
        return self._promps_dict[key]

        
class BaseComponent:
    '''Component base. Look like reactjs.'''

    def __init__(self, **promps) -> None:
        '''
            :promps Are the parameters passed to the component
        '''
        self.promps = Promps(**promps)

    @abstractclassmethod
    def update(self):
        '''Update component.'''
        pass

    @abstractclassmethod
    def render(self):
        '''Static render component.'''
        pass