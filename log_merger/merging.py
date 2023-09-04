from collections.abc import Sequence
import heapq
import itertools
from typing import TypeVar, Callable, Any

T = TypeVar("T")
KeyFunction = Callable[[T], Any]


class Merger:
    """
    Class that take a list of iterators and a key function, and yields each key value
    returned by calling that function on an item from that iterable and all the items from
    all the lists that have that value.

    Uses a heap to pull values from the multiple iterators, and itertools.groupby to combine
    values that are shared across multiple iterators by key value.
    """
    def __init__(self, seq_list: list[T], key_function: KeyFunction | None = None):
        self.seq_list = seq_list
        self.key_function = key_function or (lambda x: x)

        # compose an iterator that groups common entries returned from the heap that came from
        # different iterators
        self.heap_iter = itertools.groupby(
            heapq.merge(*self.seq_list, key=key_function),
            key=key_function
        )

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self.heap_iter)
        except IndexError:
            raise StopIteration


if __name__ == '__main__':
    list1 = "ACEFG"
    list2 = "BCCDGKR"
    m = Merger([list1, list2])
    m = Merger([iter(list1), iter(list2)])
    m = Merger([(c for c in list1), (c for c in list2)])

    for key, items in m:
        print(list(items))

    label = lambda s, seq: ((s, obj) for obj in seq)

    m = Merger([label("1", list1), label("2", list2)], key_function=lambda x: x[1])
    for key, items in m:
        print(key, list(items))

