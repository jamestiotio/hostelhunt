# Initial automation setup script to add tokens from text files to Firestore
# Created by James Raphael Tiovalen (2019)

# Import libraries
from google.cloud import firestore
import credentials

# Establish Firestore Client connection
db = firestore.Client()


# Parse data from text files and store as dictionaries
def parser(color):
    colored_tokens = {}
    for token in open(f"{color}_tokens.txt", "r"):
        token = token.rstrip('\n')
        colored_tokens[f'{token}'] = {
            u'claimant': u'', u'claimed': False, u'hash': u'', u'first_hint': u'', u'second_hint': u'', u'third_hint': u''}

    # Add dictionary to Firestore database (overwrite mode)
    db.collection(u'tokens').document(f'{color}').set(colored_tokens)


# Add entries to Firestore database
for i in ['blue', 'green', 'red', 'yellow']:
    parser(i)
