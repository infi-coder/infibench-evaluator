
def split(n, k):
    d,r = divmod(n, k)
    return [d+1]*r + [d]*(k-r)

def split_even(n, k):
    return [2 * x for x in split(n // 2, k)]


assert split_even(100, 3) == divideNumber(100, 3)
assert split_even(1000, 3) == divideNumber(1000, 3)
assert split_even(10000, 5) == divideNumber(10000, 5)
assert split_even(666, 7) == divideNumber(666, 7)