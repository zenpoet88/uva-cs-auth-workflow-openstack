import random
import string
 
def generate_password(length):
    # Generate a list of random characters
    characters = [random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(length)]
    # Shuffle the list of characters
    random.shuffle(characters)
    # Return the shuffled list of characters as a string
    return ''.join(characters)
