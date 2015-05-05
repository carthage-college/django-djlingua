from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

urlpatterns = patterns('djlingua.students.views',
    url(
        r'^students/getstudentexams$',
        'getstudentexams', name="getstudentexams"
    ),
    url(
        r'^students/searchwithincourse$',
        'getjquerystudents', name="getjquerystudents"
    ),
    url(
        r'^students/addtoexamrec$',
        'addtoexamrec', name="addtoexamrec"
    ),
    url(
        r'^students/removefromexamrec$',
        'removefromexamrec', name="removefromexamrec"
    ),
    url(
        r'^students/prepopulate$',
        'prepopulatestudents', name="prepopulatestudents"
    ),
    url(
        r'^students/getcourses$',
        'getcourses', name='getcourses'
    ),
    url(
        r'^$',
        TemplateView.as_view(template_name="forms/index.html")
    )
)
