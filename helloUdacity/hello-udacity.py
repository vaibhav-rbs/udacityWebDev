import os
import re
import cgi
from string import letters

import webapp2
import jinja2
from google.appengine.ext import db

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASSWORD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)
def escape_html(s):
    return cgi.escape(s, quote=True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

def valid_username(username):
    return username and USER_RE.match(username)

def valid_password(password):
    return password and PASSWORD_RE.match(password)

def valid_email(email):
    return not email or EMAIL_RE.match(email)

form = """
        <!DOCTYPE html>
        <html>
        <head>
        <title>Unit 2 Rot 13</title>
        </head>
        <body>
        <h2>Enter some text to ROT13:</h2>
        <form method="post">
        <textarea name="text" style="height: 100px; width: 400px; ">
        %(text)s
        </textarea>
        <br>
        <input type="submit">
        </form>
        </body>
        </html>
       """

class MainPage(webapp2.RequestHandler):

    def write_form(self, text = ''):
        self.response.out.write(form % {'text': escape_html(text)})

    def get(self):
        self.write_form()

    def post(self):
        content = self.request.get('text').encode('rot13')
        self.write_form(content)

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.response.out.write(render_str(template, **kw))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

class LoginPage(BaseHandler):

    def get(self):
        self.render('signup.html')

    def post(self):
        hasError = False
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        # These params are send back to rendering,
        params = dict(username = username, email = email)

        if not valid_username(username):
            params['error_username'] = "Thats not a valid user name."
            hasError = True

        if not valid_password(password):
            params['error_username'] = "Thats not a valid password."
            hasError = True
        elif password != verify:
            params['error_verify'] = "Password do not match."
            hasError = True

        if not valid_email(email):
            params['error_email'] = "Thats not a valid email"
            hasError = True

        if hasError:
            self.render("signup.html",**params)
        else:
            self.redirect('/welcome?username='+username)

class welcome(BaseHandler):
    def get(self):
        username = self.request.get('username')
        if valid_username(username):
            self.render('welcome.html',username = username)
        else:
            self.redirect('/sign')

app = webapp2.WSGIApplication([('/', MainPage),
                              ('/sign', LoginPage),
                              ('/welcome',welcome)],
                              debug=True)
