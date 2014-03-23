import os
import webapp2
import jinja2
import urllib2
from xml.dom import minidom

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

art_key = db.Key.from_path('ASCIIChan', 'arts')

class Handler(webapp2.RequestHandler):

    def write(self, *args,**kwargs):
        self.response.out.write(*args,**kwargs)

    def render_str(self,template,**kwargs):
        t = jinja_env.get_template(template)
        return t.render(kwargs)

    def render(self,template,**kwargs):
        self.write(self.render_str(template, **kwargs))
    
    @classmethod
    def getCoord(cls,ip):
        ip = "4.2.2.2"
        IP_URL  = "http://api.hostip.info/?ip="
        url = IP_URL + ip
        content  = None
        try:
            content  = urllib2.urlopen(url).read()
            if content:
                d = minidom.parseString(content)
                coords = d.getElementsByTagName("gml:coordinates")
                if coords and coords[0].childNodes[0].nodeValue:
                    lon, lat = coords[0].childNodes[0].nodeValue.split(',')
                    return db.GeoPt(lat, lon)
        except urllib2.URLError:
            return

    @classmethod
    def gmapImg(cls,points):
        GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=380x263&sensor=false&"
        markers = '&'.join('markers=%s,%s' % (p.lat, p.lon) for p in points)
        return GMAPS_URL + markers


class Art(db.Model):
    title = db.StringProperty(required = True)
    art = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    coords = db.GeoPtProperty()

class MainPage(Handler):

    def renderFront(self,title="",art="",error=""):
        arts = db.GqlQuery("SELECT * from Art "
                           "WHERE ANCESTOR IS :1 "
                           "ORDER BY created DESC "
                           "LIMIT 10",
                           art_key)
        # prevent the running od multiple quries. 
        arts = list(arts)
        points = []
        for a in arts:
            if a.coords:
                points.append(a.coords)
                
        imageURL = None
        if points:
            imageURL = Handler.gmapImg(points)
        self.render(
            "front.html",title=title,art=arts,error=error,imageURL=imageURL)

    def get(self):
        self.renderFront()
    
    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")
        if title and art:
            a = Art(title=title, art = art)
            a.put()
            coords = Handler.getCoord(self.request.remote_addr)
            if coords:
                a.coords = coords
            a.put()
            self.redirect("/")
        else:
            error = "hey we need both title and artwork"
            self.renderFront(title=title,art=art,error=error)
app = webapp2.WSGIApplication([('/', MainPage)], debug=True)
