_db = {}
_id = 1


def create_user(user):
    global _id
    new_user = {
        "id": _id,
        "username": user.username,
        "email": user.email,
    }
    _db[_id] = new_user
    _id += 1

    return new_user


def get_user(user_id: int):
    return _db.get(user_id)
