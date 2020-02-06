from google.cloud import firestore
import credentials
import fnmatch
import datetime
import secrets


# We use Cloud Firestore instead of Realtime Database since Firestore supports more query flexibility (better arrays!)
# Read more here: https://firebase.googleblog.com/2018/08/better-arrays-in-cloud-firestore.html
# We do not use asyncio since coroutines take too much time and threads require many event loops (we need numerous functions and for our current scale, it should be fine)
class FirebaseConnector:
    def __init__(self):
        # Establish Firestore Client connection
        self.db = firestore.Client()

    def get_all_tokens(self):
        tokens = []
        colors = self.db.collection(u'tokens').stream()
        for color in colors:
            tokens.extend(list(color.to_dict().keys()))

        return tokens

    def get_current_users(self):
        current_users = self.db.collection(u'participants').stream()

        return [user.id for user in current_users]

    def add_user(self, user_id, first_name):
        self.db.collection(u'participants').document(f'{user_id}').set({
            u'last_hint': None,
            u'name': f'{first_name}',
            u'student_id': 0
        })
    
    def get_name(self, user_id):
        user = self.db.collection(u'participants').document(f'{user_id}')

        try:
            return user.get().to_dict()['name']
            
        except TypeError as e:
            if len(e.args) > 0 and e.args[0] == "'NoneType' object is not subscriptable":
                return 0
            else:
                raise e

    def get_all_current_student_id(self):
        student_ids = []
        current_users = self.db.collection(u'participants').stream()
        for user in current_users:
            student_ids.append(user.to_dict()['student_id'])

        return student_ids

    def get_student_id(self, user_id):
        user = self.db.collection(u'participants').document(f'{user_id}')

        try:
            return user.get().to_dict()['student_id']
            
        except TypeError as e:
            if len(e.args) > 0 and e.args[0] == "'NoneType' object is not subscriptable":
                return 0
            else:
                raise e
        

    def update_student_id(self, user_id, student_id):
        self.db.collection(u'participants').document(
            f'{user_id}').set({u'student_id': student_id}, merge=True)

    def get_last_hint_time(self, user_id):
        user = self.db.collection(u'participants').document(f'{user_id}')

        return user.get().to_dict()['last_hint']

    def get_hint(self):
        tokens = []
        colors = self.db.collection(u'tokens').stream()
        for color in colors:
            tokens.append(color.to_dict())

        unclaimed_hints = []
        for color in tokens:
            for token, value in color.items():
                if value['claimed'] == False:
                    for order in ['first_hint', 'second_hint', 'third_hint']:
                        unclaimed_hints.append(value[order])

        try:
            # Select a random unclaimed hint
            return secrets.choice(unclaimed_hints)

        # Catch specific error
        except IndexError as e:
            if len(e.args) > 0 and e.args[0] == 'Cannot choose from an empty sequence':
                return ''
            else:
                raise e

    def update_last_hint_time(self, user_id, time):
        self.db.collection(u'participants').document(
            f'{user_id}').set({u'last_hint': time}, merge=True)

    def get_unclaimed_tokens(self):
        tokens = []
        colors = self.db.collection(u'tokens').stream()
        for color in colors:
            tokens.append(color.to_dict())

        unclaimed_tokens = []
        for color in tokens:
            for token, value in color.items():
                if value['claimed'] == False:
                    unclaimed_tokens.append(token)

        return unclaimed_tokens

    def get_all_users(self):
        all_users = []
        users = self.db.collection(u'participants').stream()

        for user in users:
            all_users.append(user.id)

        return all_users

    def claim_token(self, user_id, token, verification_hash):
        color = self.db.collection(u'tokens').where(
            f'`{token}`.`claimed`', '==', False).stream()
        color = [i.id for i in color][0]
        self.db.collection(u'tokens').document(f'{color}').set({
            f'{token}': {
                u'claimant': f'{user_id}',
                u'claimed': True,
                u'hash': f'{verification_hash}'
            }
        }, merge=True)

    def get_all_hash(self):
        tokens = []
        colors = self.db.collection(u'tokens').stream()
        for color in colors:
            tokens.append(color.to_dict())

        hashes = []
        for color in tokens:
            for token, value in color.items():
                if value['claimed'] == True:
                    hashes.append(value['hash'])

        return hashes
