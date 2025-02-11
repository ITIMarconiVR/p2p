from flask_login import UserMixin

from db import get_db

class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

    @staticmethod
    def get(user_id):

        db = get_db()
        cursor = db.cursor(dictionary=True)
        #cursor = db.cursor()
        cursor.execute( "SELECT * FROM utentiws WHERE id = %s", (user_id,) )
        user = cursor.fetchone()
        if not user:
            return None
        #print(user)
        us = User(
            id_=user['id'], name=user['name'], email=user['email'], profile_pic=user['profile_pic']
        )
        return us
