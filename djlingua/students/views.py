from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse

from djzbar.utils.informix import do_sql

import datetime, json

DEBUG=settings.INFORMIX_DEBUG
EARL=settings.INFORMIX_EARL


def getjquerystudents(request):
    q = request.GET.get('q', '')

    def isInt(value):
        try:
           return int(value)
        except:
           return 0

    sid = isInt(q)

    now = datetime.datetime.now()
    currentYear = now.year
    if now.month>=9:
        currentYear = now.year+1

    sqlByIdNumAndName = '''
        SELECT
            id_rec.firstname, id_rec.lastname, id_rec.fullname, id_rec.id,
            trunc(stu_stat_rec.cum_earn_hrs,0) as year1
        FROM
            id_rec, stu_stat_rec
        WHERE
            id_rec.id = "{}"
        AND
            id_rec.id = stu_stat_rec.id
        AND
            (stu_stat_rec.yr = "{}" OR stu_stat_rec.yr = "{}")
        UNION
            SELECT
                id_rec.firstname, id_rec.lastname, id_rec.fullname, id_rec.id,
                trunc(stu_stat_rec.cum_earn_hrs,0) as year1
            FROM
                id_rec, stu_stat_rec
            WHERE
                lower(id_rec.lastname) LIKE lower("{}%%")
            AND
                id_rec.id = stu_stat_rec.id
            AND
                (stu_stat_rec.yr = "{}" OR stu_stat_rec.yr = "{}")
        UNION
            SELECT
                id_rec.firstname, id_rec.lastname, id_rec.fullname,
                id_rec.id, adm_rec.plan_enr_yr as year1
            FROM
                adm_rec, id_rec
            WHERE
                adm_rec.id = id_rec.id
            AND
                adm_rec.id = "{}"
            AND
                (adm_rec.plan_enr_yr = "{}" OR adm_rec.plan_enr_yr = "{}")
        UNION
            SELECT
                id_rec.firstname, id_rec.lastname, id_rec.fullname,
                id_rec.id, adm_rec.plan_enr_yr as year1
            FROM
                id_rec, adm_rec
            WHERE
                lower(id_rec.lastname) LIKE lower("{}%%")
            AND
                id_rec.id = adm_rec.id
            AND
                (adm_rec.plan_enr_yr = "{}" OR adm_rec.plan_enr_yr = "{}")
    '''.format(
        int(sid), int(currentYear), int(currentYear-1), q, int(currentYear),
        int(currentYear-1), int(sid), int(currentYear),int(currentYear+1),
        q,int(currentYear),int(currentYear+1)
    )

    students = do_sql(sqlByIdNumAndName, key=DEBUG, earl=EARL)

    return render(
        request, 'students/search.html', {'students':students,}
    )


def getcourses(request):
    sql = '''
        SELECT
            exam, txt
        FROM
            exam_table
        WHERE
            lbl1 = "PLACEMENT" order by exam
    '''
    courses = do_sql(sql, key=DEBUG, earl=EARL)

    return render(
        request, 'students/getcourses.html', {'courses':courses,}
    )


def getstudentexams(request):
    q = request.POST.get('student', None)
    def isInt(value):
        try:
           return int(value)
        except:
           return 0
    # hold onto the student's id (if a number was entered),
    # or zero (if a name was entered)
    studentID = isInt(q)

    sqlExamsForStudent = '''
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
            id_rec.id = "{}"
    '''.format(studentID)

    exams = do_sql(sqlExamsForStudent, key=DEBUG, earl=EARL)

    sqlAllExams = '''
        SELECT
            exam, txt
        FROM
            exam_table
        WHERE
            lbl1 = "PLACEMENT"
        ORDER BY
            exam
    '''
    allexams = do_sql(sqlAllExams, key=DEBUG, earl=EARL)

    return render(
        request, 'students/studentexams.html', {
            'exams':exams, 'allexams':allexams,
            'panel':'searchByStudent','cid':studentID
        }
    )


def prepopulatestudents(request):
    q = request.GET.get('q', '')
    sql = '''
        SELECT
            exam_rec.id, exam_rec.cmpl_date, id_rec.firstname, id_rec.lastname
        FROM
            exam_rec, id_rec
        WHERE
            exam_rec.ctgry = "{}"
        AND
            exam_rec.id = id_rec.id
        AND
            (exam_rec.remark != "Courses Added" OR exam_rec.remark IS NULL)
        ORDER BY
            id_rec.lastname DESC, id_rec.firstname DESC
    '''.format(q)
    students = do_sql(sql, key=DEBUG, earl=EARL)

    return render(
        request, 'students/prepopulatestudents.html',
        {'students':students,}
    )


def addtoexamrec(request):
    ctgry = request.POST.get('courseCode', '')
    studentID = request.POST.get('student', '')
    panel = request.POST.get('panel', '')
    # before we add a student-exam record, we check to see if that student
    # already has an exam record for the same language, indicated by the same
    # first letter of ctgry
    ctgryFirst=ctgry[:1]

    '''
    sql = """
        SELECT * FROM exam_rec WHERE id = '{}' AND ctgry LIKE '{}%%'
    """.format(studentID, ctgryFirst)
    '''
    sql = '''
        SELECT
            *
        FROM
            exam_rec
        WHERE
            id = '{}'
        AND
            ctgry MATCHES '{}[0-9][0-9][0-9]'
    '''.format(studentID, ctgryFirst)

    duplicates = do_sql(sql, key=DEBUG, earl=EARL)
    numRows=0;
    duplicateCtgry=''
    for d in duplicates:
        numRows = numRows+1
        duplicateCtgry=d.ctgry

    if numRows == 0:
        NOW = str(datetime.datetime.now().strftime('%m/%d/%Y'))
        retVal = {
            'stat':'success', 'exam':ctgry, 'studentID':studentID,'panel':panel
        }
        sql = '''
            INSERT INTO
                exam_rec (
                    ctgry, id, yr, cmpl_date, score1, site, sess, score2,
                    score3, score4, score5, score6, self_rpt, conv_exam_no
                )
            VALUES (
                "{}", "{}", "0", "{}", "98", "CART", "", "0", "0", "0", "0",
                "0", "N", "0"
            )
        '''.format(ctgry, studentID, NOW)
        do_sql(sql, key=DEBUG, earl=EARL)
    else:
        retVal = {'stat':'failed', 'exam':ctgry, 'studentID':studentID}
    return HttpResponse(
        json.dumps(retVal), content_type='text/plain; charset=utf-8'
    )


def removefromexamrec(request):

    courseCode = request.POST.get('classCode', '')
    studentID = request.POST.get('studentID', '')
    panel = request.POST.get('panel', '')

    sql = '''
        DELETE FROM exam_rec WHERE id='{}' AND ctgry='{}'
    '''.format(studentID, courseCode)
    do_sql(sql, key=DEBUG, earl=EARL)

    sql = '''
        SELECT
            firstname, lastname
        FROM
            id_rec
        WHERE
            id_rec.id = "{}"
    '''.format( studentID)
    nameSQL = do_sql(sql
, key=DEBUG, earl=EARL)
    stuName=''
    for name in nameSQL:
        stuName = name.firstname + " " + name.lastname

    sql = '''
        SELECT txt FROM exam_table WHERE exam = "{}"
    '''.format(courseCode)
    courseNames = do_sql(sql, key=DEBUG, earl=EARL)
    courseName=''
    for c in courseNames:
        courseName = c.txt

    retVal = {
        'studentName':stuName, 'className':courseName, 'panel':panel
    }

    return HttpResponse(
        json.dumps(retVal), content_type='text/plain; charset=utf-8'
    )
