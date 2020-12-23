import re
import json
import logging
import requests

from os import urandom
from string import punctuation
from unidecode import unidecode

# CONSTANTS
AUTHOR = 'author'
AUTHORS = 'authors'
BASE_URL = 'https://poetrydb.org'
CHARS_TO_DIGIT = 'olzeasgtbp'
DIGITS = '0123456789'
FUNCTORS = '\s+(an|and|as|by|if|in|into|is|it|not|of|on|or|th|the|to|with)(\s+)'
MIN_DICT_LEN = 5000
MIN_PWORD_LEN = 12
SPECIAL_CHARS = punctuation.replace('`', '')

log = logging.getLogger(__name__)


def gen_pword():
    """
        Generate strong passwords using random
        corpus assembled from PoetryDB API.
    """

    pword = []
    secure_pword = ''

    # Generate dictionary
    dictionary = get_dict()

    # Create sentence base
    while len(''.join(pword)) < MIN_PWORD_LEN:
        word = dictionary[rand_int(2, len(dictionary))]
        pword.append(word)

    # Random letter conversion and capitalization
    for word in pword:
        word = list(word)
        word_len = len(word)
        max_conversions = rand_int(mod=word_len / 4) + 1

        while max_conversions > 0:
            r = rand_int(mod=6)
            if r > 2:
                continue

            letters = list(word)
            r_idx = rand_int(mod=len(word))
            letter = letters[r_idx]

            # Flip a coin to decide if we will replace with a digit or capitalize
            coin_flip = rand_int(mod=2)
            trans_from = CHARS_TO_DIGIT if coin_flip else letter
            trans_to = DIGITS if coin_flip else letter.upper()
            word[r_idx] = letter.translate(str.maketrans(trans_from, trans_to))

            max_conversions -= 1
            if max_conversions <= 0:
                break

        # Append special character to beginning or end of word
        r = rand_int(mod=word_len + 1)

        if r in [0, word_len]:
            word.insert(r, SPECIAL_CHARS[rand_int(mod=len(SPECIAL_CHARS))])

        word = ''.join(word)
        secure_pword += word

    log.info(f'PASSWORD: {secure_pword}')


def get_authors():
    """
        Call PoetryDB /authors endpoint. Note that
        this list is quite limited at the moment.
    """

    # Pull authors
    r = requests.get(f"{BASE_URL}/{AUTHORS}")
    if r.status_code != 200:
        log.warning(f'{r.status_code} response. Exiting.')
        return

    author_list = r.json()
    if not author_list or not author_list.get('authors'):
        log.warning('API returned blank response. Retry in a few minutes.')
        return

    return author_list.get('authors')


def get_dict():
    """
        Call PoetryDB /author/<author> endpoint,
        select poems randomly, combine into single
        dictionary.
    """

    dictionary = []
    dict_len = 0
    poems = get_poems()

    while dict_len <= MIN_DICT_LEN:
        # Grab a poem at random and add to dict until we hit MIN_DICT_LEN
        lines = poems[rand_int(mod=len(poems))].get('lines')
        poem = ' '.join(lines).lower()

        # Normalize to remove accents, strokes, etc
        poem = unidecode(poem)

        # Strip punctuation and numbers
        to_strip = punctuation + DIGITS
        poem = poem.translate(str.maketrans(' ', ' ', to_strip))

        # Strip out functors
        poem = re.sub(FUNCTORS, ' ', poem)

        # Strip out one-character words
        poem = re.sub(r'(?:^| )\w(?:$| )', ' ', poem)

        dictionary.append(poem)
        dict_len += len(poem)

    dictionary = ' '.join(dictionary)

    # Strip whitespace
    return re.sub('\s\s+', ' ', dictionary).split(' ')


def rand_int(bytes=1, mod=None):
    """
        Generate secure random integer.

        bytes: length of hex
        mod: base by which to normalize
    """
    i = int(urandom(bytes).hex(),16)

    if mod is not None:
        i = i % mod

    return i


def get_poems():
    try:
        with open('poems.json') as fh:
            return json.loads(fh.read())
    except IOError as e:
        log.info('No poems found. Retrieving corpus...')
        poems = []
        for author in get_authors():
            r = requests.get(f'{BASE_URL}/{AUTHOR}/{author}')
            if r.status_code != 200:
                log.warning(f'{r.status_code} response. Exiting.')
                return

            poems = poems + r.json()

        with open('poems.json', 'w+') as fh:
            fh.write(json.dumps(poems))

        log.info('Corpus created and saved to poems.json.')
        return poems


if __name__ == '__main__':
    gen_pword()
