def f(rest, b, last):
    for i, l in enumerate(last):
        if l in b:
            if b.index(l) < len(rest):
                last[i] = rest[b.index(l)]
    return last

rest1 = [1, 3, 5, 7, 9, 2, 4, 6, 8, 10]
b1 = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
last1 = [5, 10, 15, 12, 9, 27]
assert f(rest1, b1, last1) == ReplaceElementsByIndex(rest1, b1, last1)

