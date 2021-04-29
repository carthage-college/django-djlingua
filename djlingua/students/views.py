# -*- coding: utf-8 -*-

import datetime
import json
import logging

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse

from djimix.core.database import get_connection
from djimix.core.database import xsql

logger = logging.getLogger(__name__)


def _is_cid(instance):
    """Return college id (if a number), or zero (if a name was entered)."""
    if instance.isnumeric():
        instance = int(instance)
    else:
        instance = 0
    return instance


def getjquerystudents(request):
    """Fetch all relevant students."""
    query = request.GET.get('q', '')

    cid = _is_cid(query)

    now = datetime.datetime.now()
    currentYear = now.year
    if now.month >= 9:
        currentYear = now.year + 1

    sqlByIdNumAndName = """
        SELECT
            id_rec.firstname, id_rec.lastname, id_rec.fullname, id_rec.id,
            trunc(stu_stat_rec.cum_earn_hrs,0) as year1
        FROM
            id_rec, stu_stat_rec
        WHERE
            id_rec.id = "{0}"
        AND
            id_rec.id = stu_stat_rec.id
        AND
            (stu_stat_rec.yr = "{1}" OR stu_stat_rec.yr = "{2}")
        UNION
            SELECT
                id_rec.firstname, id_rec.lastname, id_rec.fullname, id_rec.id,
                trunc(stu_stat_rec.cum_earn_hrs,0) as year1
            FROM
                id_rec, stu_stat_rec
            WHERE
                lower(id_rec.lastname) LIKE lower("{3}%%")
            AND
                id_rec.id = stu_stat_rec.id
            AND
                (stu_stat_rec.yr = "{4}" OR stu_stat_rec.yr = "{5}")
        UNION
            SELECT
                id_rec.firstname, id_rec.lastname, id_rec.fullname,
                id_rec.id, adm_rec.plan_enr_yr as year1
            FROM
                adm_rec, id_rec
            WHERE
                adm_rec.id = id_rec.id
            AND
                adm_rec.id = "{6}"
            AND
                (adm_rec.plan_enr_yr = "{7}" OR adm_rec.plan_enr_yr = "{8}")
        UNION
            SELECT
                id_rec.firstname, id_rec.lastname, id_rec.fullname,
                id_rec.id, adm_rec.plan_enr_yr as year1
            FROM
                id_rec, adm_rec
            WHERE
                lower(id_rec.lastname) LIKE lower("{9}%%")
            AND
                id_rec.id = adm_rec.id
            AND
                (adm_rec.plan_enr_yr = "{10}" OR adm_rec.plan_enr_yr = "{11}")
    """.format(
        int(cid),
        int(currentYear),
        int(currentYear - 1),
        q,
        int(currentYear),
        int(currentYear - 1),
        int(cid),
        int(currentYear),
        int(currentYear + 1),
        q,
        int(currentYear),
        int(currentYear + 1),
    )
    if settings.DEBUG:
        logger.debug(sqlByIdNumAndName)
    with get_connection() as connection:
        students = xsql(sqlByIdNumAndName, connection).fetchall()

    return render(request, 'students/search.html', {'students': students})


def getcourses(request):
    """Fetch all courses that are related to language placement."""
    sql = """
        SELECT
            exam, txt
        FROM
            exam_table
        WHERE
            lbl1 = "PLACEMENT" order by exam
    """
    if settings.DEBUG:
        logger.debug(sql)
    with get_connection() as connection:
        courses = xsql(sql, connection).fetchall()

    return render(request, 'students/getcourses.html', {'courses': courses})


def getstudentexams(request):
    """Obtain the student exams."""
    query = request.POST.get('student', None)
    cid = _is_cid(query)
    sqlExamsForStudent = """
        SELECT
            exam_rec.id, trim(id_rec.firstname) as first,
            trim(id_rec.lastname) as last, exam_rec.ctgry,
            trim(exam_table.txt) as exam, exam_rec.cmpl_date,
            trim(exam_rec.remark) as remark, trim(exam_table.lbl1) as label,
            adm_rec.plan_enr_yr, adm_rec.plan_enr_sess
        FROM
            id_rec
        LEFT JOIN (
                exam_rec
                LEFT JOIN
                    exam_table
                ON
                    exam_rec.ctgry = exam_table.exam
                AND
                    exam_table.lbl1= "PLACEMENT"
            )
            ON id_rec.id = exam_rec.id
        LEFT JOIN
            adm_rec on id_rec.id = adm_rec.id
        WHERE
            id_rec.id = "{0}"
    """.format(cid)

    if settings.DEBUG:
        logger.debug(sqlExamsForStudent)
    with get_connection() as connection:
        exams = xsql(sqlExamsForStudent, connection).fetchall()

    sqlAllExams = """
        SELECT
            exam, txt
        FROM
            exam_table
        WHERE
            lbl1 = "PLACEMENT"
        ORDER BY
            exam
    """
    if settings.DEBUG:
        logger.debug(sqlAllExams)
    with get_connection() as connection:
        allexams = xsql(sqlAllExams, connection).fetchall()

    return render(
        request,
        'students/studentexams.html',
        {
            'exams': exams,
            'allexams': allexams,
            'panel': 'searchByStudent',
            'cid': cid,
        }
    )


def prepopulatestudents(request):
    """Return students to prepopulate the user interface."""
    query = request.GET.get('q', '')
    sql = """
        SELECT
            exam_rec.id, exam_rec.cmpl_date, id_rec.firstname, id_rec.lastname
        FROM
            exam_rec, id_rec
        WHERE
            exam_rec.ctgry = "{0}"
        AND
            exam_rec.id = id_rec.id
        AND
            (exam_rec.remark != "Courses Added" OR exam_rec.remark IS NULL)
        ORDER BY
            id_rec.lastname DESC, id_rec.firstname DESC
    """.format(query)
    if settings.DEBUG:
        logger.debug(sql)
    with get_connection() as connection:
        students = xsql(sql, connection).fetchall()

    return render(
        request,
        'students/prepopulatestudents.html',
        {'students':students},
    )


def addtoexamrec(request):
    """Insert data into the exam_rec table."""
    ctgry = request.POST.get('courseCode', '')
    cid = request.POST.get('student', '')
    panel = request.POST.get('panel', '')
    # before we add a student-exam record, we check to see if that student
    # already has an exam record for the same language, indicated by the same
    # first letter of ctgry
    ctgryFirst=ctgry[:1]

    sql = """
        SELECT
            *
        FROM
            exam_rec
        WHERE
            id = "{0}"
        AND
            ctgry MATCHES "{1}[0-9][0-9][0-9]"
    """.format(cid, ctgryFirst)

    if settings.DEBUG:
        logger.debug(sql)
    with get_connection() as connection:
        duplicates = xsql(sql, connection).fetchall()
    numRows = 0
    duplicateCtgry = ''
    for dupe in duplicates:
        numRows = numRows + 1
        duplicateCtgry = dupe.ctgry

    if numRows == 0:
        #now = str(datetime.datetime.now().strftime('%m/%d/%Y'))
        now = str(datetime.datetime.now().strftime('%Y-%m-%d'))
        retVal = {
            'stat': 'success',
            'exam': ctgry,
            'studentID': cid,
            'panel': panel,
        }
        sql = """
            INSERT INTO
                exam_rec (
                    ctgry, id, yr, cmpl_date, score1, site, sess, score2,
                    score3, score4, score5, score6, self_rpt, conv_exam_no
                )
            VALUES (
                "{0}", "{1}", "0", TODAY, "98", "CART", "", "0", "0", "0", "0",
                "0", "N", "0"
            )
        """.format(ctgry, cid)
        if settings.DEBUG:
            logger.debug(sql)
        with get_connection() as connection:
            xsql(sql, connection)
    else:
        retVal = {'stat': 'failed', 'exam': ctgry, 'studentID': cid}
    return HttpResponse(
        json.dumps(retVal), content_type='text/plain; charset=utf-8',
    )


def removefromexamrec(request):
    """Remove data from the exam_rec table."""
    courseCode = request.POST.get('classCode', '')
    cid = request.POST.get('studentID', '')
    panel = request.POST.get('panel', '')

    sql = """
        DELETE FROM exam_rec WHERE id='{0}' AND ctgry='{1}'
    """.format(cid, courseCode)
    if settings.DEBUG:
        logger.debug(sql)
    with get_connection() as connection:
        xsql(sql, connection)

    sql = """
        SELECT
            firstname, lastname
        FROM
            id_rec
        WHERE
            id_rec.id = "{0}"
    """.format(cid)
    if settings.DEBUG:
        logger.debug(sql)
    with get_connection() as connection:
        nameSQL = xsql(sql, connection).fetchall()
    stuName = ''
    for name in nameSQL:
        stuName = '{0} {1}'.format(name.firstname, name.lastname)

    sql = """
        SELECT txt FROM exam_table WHERE exam = "{0}"
    """.format(courseCode)
    if settings.DEBUG:
        logger.debug(sql)
    with get_connection() as connection:
        courseNames = xsql(sql, connection).fetchall()
    courseName = ''
    for course in courseNames:
        courseName = course.txt

    retVal = {'studentName': stuName, 'className': courseName, 'panel': panel}

    return HttpResponse(
        json.dumps(retVal), content_type='text/plain; charset=utf-8',
    )
