import os
import re
import webapp2
import jinja2
import hmac

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
        autoescape = True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class blogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.response.out.write(self.render_str(template, **kw))

    @classmethod
    def blogKey(cls, name = 'default'):
        return db.Key.from_path('blogs',name)

# db class for blog
class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now= True)

    def render(self):
        self._render_text = self.content.replace('\n','<br>')
        return render_str("post.html",p=self)


class blogFront(blogHandler):
    def get(self):
        posts = Post.all().order('-created')
        self.render('front.html',posts = posts)

class postPage(blogHandler):
    def get(self,post_id):
        key = db.Key.from_path(
                'Post',int(post_id),parent=blogHandler.blogKey())
        post = db.get(key)
        if not post:
            self.error(404)
            return
        self.render("permalink.html",post=post)

class newPost(blogHandler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')
        if subject and content:
            p = Post(parent = blogHandler.blogKey(),
                    subject=subject,content=content)
            p.put()
            self.redirect("/blog/%s" % str(p.key().id()))
        else:
            error = "subject and content please"
            self.render("newpost.html",
                    subject = subject,content=content,error=error)


# db class for user 
class user(db.Model):
    name       =  db.StringProperty(required = True)
    p_word     =  db.StringProperty(required = True)
    ip_address =  db.StringProperty(required=True)
    email      =  db.StringProperty()

    @classmethod
    def queryKey(cls, ancestorKey = 'default'):
        return cls.query(ancestor=ancestorKey)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

SECRET = "mySecret"
def hash_str(s):
    return hmac.new(SECRET,s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
   val = h.split('|')[0]
   if h == make_secure_val(val):
       return val

PASSWORDSECRET = "myPassowrdSecret"
def hash_pass(s):
    return hmac.new(PASSWORDSECRET,s).hexdigest()

class Signup(blogHandler):

    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        username = self.request.get('username')
        password = self.request.get('password')
        verify   = self.request.get('verify')
        email    = self.request.get('email')
        hashed   = hash_pass(password)
        ip       = self.request.remote_addr
        params   = dict(username = username,email = email)

        account  = user(name=username,p_word=hashed, ip_address=ip, email=email)
        account.put()

        if not valid_username(username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif password != verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            cookie_user    = make_secure_val(str(account.key().id()))
            self.response.headers.add_header('Set-Cookie', 
                'user_id=%s; Path=/' % cookie_user)
            self.redirect('/welcome')
            
class Login(blogHandler):
    def get(self):
        self.render("login.html")

    def post(self):
        uname = self.request.get('username')
        pword = self.request.get('password')
        userExists = db.GqlQuery(
                "SELECT * from user WHERE name=:1",uname).get()
        if userExists:
            if userExists.p_word == hash_pass(pword):
                cookie_user = make_secure_val(str(userExists.key().id()))
                self.response.headers.add_header('Set-Cookie', 
                        'user_id=%s; Path=/' % cookie_user)
                self.redirect('/welcome')
        else:
            params = {}
            params['invalid_login'] = "Invalid login"
            self.render('login.html', **params)

class Logout(blogHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie',
                'user_id=; Path=/')
        self.redirect('/blog/signup')

class Welcome(blogHandler):
    def get(self):
        try:
            user_id_cookie  = self.request.cookies.get('user_id')
            split_values    = user_id_cookie.split('|')
            id_num          = split_values[0]
            user_object     = user.get_by_id(int(id_num))
            name            = user_object.name

            if split_values[1] == hash_str(id_num):
                self.render('welcome.html', username = name)
            else:
                self.redirect('/blog/signup')
        except:
            self.redirect('/blog/signup')

app = webapp2.WSGIApplication([("/blog/?", blogFront),
                               ("/blog/([0-9]+)",postPage),
                               ("/blog/newpost", newPost), 
                               ("/blog/signup", Signup),
                               ("/blog/login", Login),
                               ("/blog/logout", Logout),
                               ("/welcome", Welcome)],debug=True)
