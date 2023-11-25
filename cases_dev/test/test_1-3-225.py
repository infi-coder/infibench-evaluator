def f(text):
    words = text.split()
    pigged_text = []
    for word in words:
        word = word[1:] + word[0] + 'ay'
        pigged_text.append(word)
    return ' '.join(pigged_text)

assert pig_latin('hello world') == f('hello world')
assert pig_latin('hello') == f('hello')
assert pig_latin('hello world!') == f('hello world!')
assert pig_latin('hello world a b c d.') == f('hello world a b c d.')