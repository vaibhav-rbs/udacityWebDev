import os
import re
import webapp2
import jinja2
import hmac
import json

from google.appengine.ext import db
from google.appengine.api import memcache

#Load templating engine and jinja env.
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
        autoescape=True)


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
SECRET = "mySecret"
PASSWORDSECRET = "myPassowrdSecret"

# Password Helper function


def valid_username(username):
    return username and USER_RE.match(username)


def valid_password(password):
    return password and PASS_RE.match(password)


def valid_email(email):
    return not email or EMAIL_RE.match(email)


def hash_str(s):
    return hmac.new(SECRET,s).hexdigest()


def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))


def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val


def hash_pass(s):
    return hmac.new(PASSWORDSECRET,s).hexdigest()


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

###############Models###############


class Department(db.Model):

    deptName = db.StringProperty(required=True)


class Supervisor(db.Model):

    name = db.StringProperty(required=True)
    number = db.PhoneNumberProperty(required=True)
    dept = db.ReferenceProperty(Department,
                                collection_name='Departments')


class Employee(db.Model):

    firstName = db.StringProperty(required=True)
    lastName = db.StringProperty(required=True)
    title = db.StringProperty(required=True)
    email = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    supervisor = db.ReferenceProperty(Supervisor,
                                      collection_name='Supervisors')


class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.response.out.write(self.render_str(template, **kw))


class CompanyDirectoryFront(BlogHandler):

    def get(self):
        memcache.flush_all()
        total_employees = db.GqlQuery("SELECT * from  Employee").get().all()
        self.render('front.html', total_employees=total_employees)


class NewDepartment(BlogHandler):
    def get(self):
        self.render("newDepartment.html")

    def post(self):
        memcache.flush_all()
        dept_no = self.request.get('deptNo')
        dept_name = self.request.get('deptName')
        departments = Department(key_name=dept_no, deptName=dept_name)
        departments.put()
        self.redirect("/companyDirectory/")


class NewSupervisor(BlogHandler):

    def get(self):
        departments = db.GqlQuery("SELECT * from Department").get().all()
        self.render("newSupervisor.html", departments=departments)

    def post(self):
        memcache.flush_all()
        supervisor_no = self.request.get('supervisorNo')
        name = self.request.get('name')
        number = self.request.get('phoneNumber')
        departmentList = self.request.get('departmentList')
        department_object = db.GqlQuery("SELECT * from Department where deptName =:1",departmentList).get().all().fetch(1)[0]
        supervisor = Supervisor(
            key_name=supervisor_no, name=name, number=number,dept=department_object)
        supervisor.put()
        self.redirect("/companyDirectory/")


class NewEmployee(BlogHandler):
    def get(self):
        supervisors = db.GqlQuery("SELECT * from Supervisor").get().all()
        self.render("newEmployee.html", supervisors=supervisors)

    def post(self):
        memcache.flush_all()
        emp_no = self.request.get('empNo')
        first_name = self.request.get('firstName')
        last_name = self.request.get('lastName')
        title = self.request.get('title')
        email = self.request.get('email')
        password = self.request.get('password')
        verify = self.request.get('verify')
        supervisor = self.request.get('supervisorSelect')
        if verify == password:
            supervisor_object = db.GqlQuery("SELECT * from Supervisor where name =:1",supervisor).get().all().fetch(1)[0]
            employee = Employee.get_or_insert(key_name=emp_no,
                                              firstName=first_name, lastName=last_name,
                                              title=title, email=email, password=password,
                                              supervisor=supervisor_object)
            if not employee:
                employee.put()
                self.redirect("/companyDirectory/")
            else:
                params = {"emp_no":emp_no}
                self.render("newEmployee.html", params=params)




app = webapp2.WSGIApplication([("/companyDirectory/", CompanyDirectoryFront),
                               ("/companyDirectory/NewEmployee", NewEmployee),
                               ("/companyDirectory/NewSupervisor", NewSupervisor),
                               ("/companyDirectory/NewDepartment", NewDepartment)], debug=True)

