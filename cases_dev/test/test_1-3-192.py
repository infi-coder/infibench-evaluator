def f(text):
    s = text.replace("-", " ").replace("_", " ")
    s = s.split()
    if len(text) == 0:
        return text
    return s[0] + ''.join(i.capitalize() for i in s[1:])

s1 = "the_stealth_warrior"
s2 = '23_fg wre sf+ w_we'
s3 = '1_2_3_4 5 6 7'
assert f(s1) == to_camel_case(s1)
assert f(s2) == to_camel_case(s2)
assert f(s3) == to_camel_case(s3)