# -*- coding: utf-8 -*-

from django.urls import include
from django.urls import path
from django.views.generic import TemplateView

from djlingua.students import views


urlpatterns = [
    path('students/getstudentexams/',
        views.getstudentexams,
        name='getstudentexams',
    ),
    path(
        'students/searchwithincourse/',
        views.getjquerystudents,
        name='getjquerystudents',
    ),
    path(
        'students/addtoexamrec/',
        views.addtoexamrec,
        name='addtoexamrec',
    ),
    path(
        'students/removefromexamrec/',
        views.removefromexamrec,
        name='removefromexamrec',
    ),
    path(
        'students/prepopulate/',
        views.prepopulatestudents,
        name='prepopulatestudents',
    ),
    path('students/getcourses/', views.getcourses, name='getcourses'),
    path('', TemplateView.as_view(template_name='home.html')),
]
