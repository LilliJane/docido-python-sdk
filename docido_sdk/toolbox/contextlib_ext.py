
from contextlib import contextmanager
import copy


@contextmanager
def restore_dict_kv(a_dict, key, copy_func=copy.deepcopy):
    """Backup an object in a with context and restore it when leaving
    the scope.

    :param a_dict:
      associative table
    :param: key
      key whose value has to be backed up
    :param copy_func: callbable object used to create an object copy.
    default is `copy.deepcopy`
    """
    exists = False
    if key in a_dict:
        backup = copy_func(a_dict[key])
        exists = True
    try:
        yield
    finally:
        if exists:
            a_dict[key] = backup
        else:
            a_dict.pop(key, None)
