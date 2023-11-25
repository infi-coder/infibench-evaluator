

def check(s):
    if not isinstance(s, str): return False
    if not s.isalnum(): return False
    if len(s) != 16:
        return False
    if 'NAA3U' not in s:
        return False
    count = 0
    for x in s:
        if x in [str(i) for i in range(10)]:
            count += 1
    if count != 3:
        return False
    return True

"""import random
import random

import random
import string

def generateRandomString():
    allowed_characters = string.ascii_letters + string.digits  # All letters and digits

    while True:
        # Generate a random 11-character string from allowed_characters
        random_part = ''.join(random.choice(allowed_characters) for _ in range(11))

        # Create the full code by inserting "NAA3U" and 3 random digits
        code = f'NAA3U{random_part}'
        code = list(code)

        # Replace 3 characters with random digits
        digit_indices = random.sample(range(0, 16), 3)
        for index in digit_indices:
            code[index] = random.choice(string.digits)

        # Convert the list back to a string
        code = ''.join(code)

        # Check if the generated code contains "NAA3U" and has exactly 3 digits
        if "NAA3U" in code and sum(1 for c in code if c.isdigit()) == 3:
            return code"""

# Example usage:


flag = False
for _ in range(3):
    tot = 0
    for _ in range(100):
        if check(generateRandomString()):
            tot += 1
    if tot >= 95:
        flag = True
        break
assert flag