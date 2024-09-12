def contains_list(full_list, sub_list) -> bool:
    sub_len = len(sub_list)
    for offset in range(len(full_list) - len(sub_list) + 1):
        if full_list[offset:offset + sub_len] == sub_list:
            return True
    return False


if __name__ == '__main__':
    assert(contains_list([1,2,3,4], [3,4]))
    assert(contains_list([1,2,3,4], [1,2,3,4]))
    assert(contains_list([1,2,3,4], [1,]))
    assert(contains_list([1,2,3,4], []))

    assert(not contains_list([1,2,3,4], [1,2,3,4,5]))
    assert(not contains_list([1,2,3,4], [2,2,3,4]))
