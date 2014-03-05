import re
class LoginPage(object):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    PASSWORD_RE = re.compile(r"^.{3,20}$")
    EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
     
    def valid_username(self,username):
        return username and LoginPage.USER_RE.match(username)

    def valid_password(self,password):
        return password and LoginPage.PASSWORD_RE.match(password)

    def valid_email(self, email):
        return not email or LoginPage.EMAIL_RE.match(email)

if __name__ == "__main__":
    x = LoginPage()
    print x.valid_username('Vaibhav')
