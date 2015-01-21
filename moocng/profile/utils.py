# -*- coding: utf-8 -*-

def get_user(id):
    from moocng.users.models import User
    return User.objects.get(id=id)	

