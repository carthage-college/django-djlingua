from django.conf.urls import include, url
from django.views.generic import TemplateView

from djlingua.students import views


urlpatterns = [
    url(
        r'^students/getstudentexams',
        views.getstudentexams, name='getstudentexams'
    ),
    url(
        r'^students/searchwithincourse',
        views.getjquerystudents, name='getjquerystudents'
    ),
    url(
        r'^students/addtoexamrec',
        views.addtoexamrec, name='addtoexamrec'
    ),
    url(
        r'^students/removefromexamrec',
        views.removefromexamrec, name='removefromexamrec'
    ),
    url(
        r'^students/prepopulate',
        views.prepopulatestudents, name='prepopulatestudents'
    ),
    url(
        r'^students/getcourses',
        views.getcourses, name='getcourses'
    ),
    url(
        r'^$',
        TemplateView.as_view(template_name='home.html')
    )
]
