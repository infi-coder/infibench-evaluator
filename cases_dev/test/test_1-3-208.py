import re
def f(text):
    pattern = re.compile("[A-Za-z0-9]+")
    return pattern.fullmatch(text)

assert f("123") == checkString("123")
assert f("abc") == checkString("abc")
assert f("abc123") == checkString("abc123")
assert f("abc123!") == checkString("abc123!")
assert f("a1bc12a3 ") == checkString("a1bc12a3 ")
assert f(" abc123") == checkString(" abc123")
assert f("abc 123") == checkString("abc 123")
assert f("abc 123 ") == checkString("abc 123 ")