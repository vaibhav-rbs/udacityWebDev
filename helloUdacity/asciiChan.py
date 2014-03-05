import os
import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

class Handler(webapp2.RequestHandler):
    def write(self, *args,**kwargs):
        self.response.out.write(*args,**kwargs)

    def render_str(self,template,**kwargs):
        t = jinja_env.get_template(template)
        return t.render(kwargs)

    def render(self,template,**kwargs):
        self.write(self.render_str(template, **kwargs))

class Art(db.Model):
    title = db.StringProperty(required = True)
    art = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

class MainPage(Handler):
    def renderFront(self,title="",art="",error=""):
        arts = db.GqlQuery("SELECT * from Art " 
                "ORDER BY created DESC")
        self.render("front.html",title=title,art=arts,error=error)

    def get(self):
        self.renderFront()
    
    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")
        if title and art:
            a = Art(title=title, art = art)
            a.put()
            self.redirect("/")
        else:
            error = "hey we need both title and artwork"
            self.renderFront(title=title,art=art,error=error)
app = webapp2.WSGIApplication([('/', MainPage)], debug=True)
