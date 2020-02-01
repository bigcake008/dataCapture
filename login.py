import requests

session = requests.Session()


class Login:
    def __init__(self, username, ua, tpl_password2):
        self.username = username
        self.ua = ua
        self.tpl_password2 = tpl_password2
