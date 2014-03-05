import os
import re
import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
        autoescape = True)

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


app = webapp2.WSGIApplication([("/blog/?", blogFront),
                               ('/blog/([0-9]+)',postPage),
                               ("/blog/newpost", newPost)], debug=True)
