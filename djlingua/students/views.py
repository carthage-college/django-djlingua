from django.conf import settings
from django.http import HttpResponse
from django.template import Context, RequestContext
from django.shortcuts import render_to_response

from djzbar.utils.informix import do_sql

import datetime, json

def getjquerystudents(request):
    q = request.GET.get("q", "")

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

    sqlByIdNumAndName = ('SELECT id_rec.firstname, id_rec.lastname, id_rec.fullname, id_rec.id, trunc(stu_stat_rec.cum_earn_hrs,0) as year1 '
      'FROM id_rec, stu_stat_rec '
      'WHERE id_rec.id = \'%s\' AND id_rec.id = stu_stat_rec.id AND (stu_stat_rec.yr = \'%s\' OR stu_stat_rec.yr = \'%s\') '
      'UNION '
      'SELECT id_rec.firstname, id_rec.lastname, id_rec.fullname, id_rec.id, trunc(stu_stat_rec.cum_earn_hrs,0) as year1 '
      'FROM id_rec, stu_stat_rec '
      'WHERE lower(id_rec.lastname) LIKE lower(\'%s%%\') AND id_rec.id = stu_stat_rec.id AND (stu_stat_rec.yr = \'%s\' OR stu_stat_rec.yr = \'%s\') '
      'UNION '
      'SELECT id_rec.firstname, id_rec.lastname, id_rec.fullname, id_rec.id, adm_rec.plan_enr_yr as year1 '
      'FROM adm_rec, id_rec '
      'WHERE adm_rec.id = id_rec.id AND adm_rec.id = \'%s\' AND (adm_rec.plan_enr_yr = \'%s\' OR adm_rec.plan_enr_yr = \'%s\' ) '
      'UNION '
      'SELECT id_rec.firstname, id_rec.lastname, id_rec.fullname, id_rec.id, adm_rec.plan_enr_yr as year1 '
      'FROM id_rec, adm_rec '
      'WHERE lower(id_rec.lastname) LIKE lower(\'%s%%\') AND id_rec.id = adm_rec.id AND (adm_rec.plan_enr_yr = \'%s\' OR adm_rec.plan_enr_yr = \'%s\')'
      % (int(sid), int(currentYear), int(currentYear-1), q, int(currentYear), int(currentYear-1), int(sid), int(currentYear),int(currentYear+1),q,int(currentYear),int(currentYear+1)))

    students = do_sql(sqlByIdNumAndName)
    context = {'students':students,}
    return render_to_response(
        'students/search.html', context, RequestContext(request)
    )

def getcourses(request):
    sql = """
        SELECT exam, txt FROM exam_table WHERE lbl1 = 'PLACEMENT' order by exam
    """
    courses = do_sql(sql)
    context = {'courses':courses,}
    return render_to_response(
        'students/getcourses.html', context, RequestContext(request)
    )


def getstudentexams(request):
    q = request.POST.get("student", None)
    def isInt(value):
        try:
           return int(value)
        except:
           return 0
    # hold onto the student's id (if a number was entered),
    # or zero (if a name was entered)
    studentID = isInt(q)

    sqlExamsForStudent = ('''SELECT exam_rec.id, trim(id_rec.firstname) as first, trim(id_rec.lastname) as last,
    exam_rec.ctgry, trim(exam_table.txt) as exam, exam_rec.cmpl_date, trim(exam_rec.remark) as remark,
    trim(exam_table.lbl1) as label, adm_rec.plan_enr_yr, adm_rec.plan_enr_sess
    FROM id_rec
        left join (exam_rec
            left join exam_table
            on exam_rec.ctgry = exam_table.exam
            AND exam_table.lbl1= "PLACEMENT"
            )
        on id_rec.id = exam_rec.id
        left join adm_rec on id_rec.id = adm_rec.id
    WHERE id_rec.id = \'%s\' '''
    % (studentID))
    exams = do_sql(sqlExamsForStudent)

    sqlAllExams = """
        SELECT exam, txt FROM exam_table WHERE lbl1 = 'PLACEMENT' order by exam
    """
    allexams = do_sql(sqlAllExams)

    return render_to_response(
        'students/studentexams.html',
        {
            'exams':exams, 'allexams':allexams, 'panel':'searchByStudent'
        },
        RequestContext(request)
    )

def prepopulatestudents(request):
    q = request.GET.get("q", "")
    sql = ('SELECT exam_rec.id, exam_rec.cmpl_date, id_rec.firstname, id_rec.lastname '
           'FROM exam_rec, id_rec '
           'WHERE exam_rec.ctgry = \'%s\' AND exam_rec.id = id_rec.id AND (exam_rec.remark != "Courses Added" OR exam_rec.remark IS NULL) '
           'ORDER BY id_rec.lastname DESC, id_rec.firstname DESC' % (q))
    students = do_sql(sql)
    return render_to_response(
        'students/prepopulatestudents.html',
        {'students':students,},
        RequestContext(request)
    )

def addtoexamrec(request):
    ctgry = request.POST.get("courseCode", "")
    studentID = request.POST.get("student", "")
    panel = request.POST.get("panel", "")
    # before we add a student-exam record, we check to see if that student
    # already has an exam record for the same language, indicated by the same
    # first letter of ctgry
    ctgryFirst=ctgry[:1]

    NOW = str(datetime.datetime.now().strftime("%m/%d/%Y"))
    #duplicates = do_sql('SELECT * FROM exam_rec WHERE id = \'%s\' AND ctgry LIKE \'%s%%\' ' % (studentID, ctgryFirst));
    duplicates = do_sql('SELECT * FROM exam_rec WHERE id = \'%s\' AND ctgry MATCHES \'%s[0-9][0-9][0-9]\' ' % (studentID, ctgryFirst));
    numRows=0;
    duplicateCtgry=""
    for d in duplicates:
        numRows = numRows+1
        duplicateCtgry=d.ctgry

    if numRows == 0:
        retVal = {'stat':'success', 'exam':ctgry, 'studentID':studentID, 'panel':panel}
        sql = ( 'INSERT INTO exam_rec (ctgry, id, yr, cmpl_date, score1, site, sess, score2, score3, score4, score5, score6, self_rpt, conv_exam_no) VALUES (\'%s\', \'%s\', \'0\', \'%s\', \'98\', \'CART\', \'\', \'0\', \'0\', \'0\', \'0\', \'0\', \'N\', \'0\') ' % (ctgry, studentID, NOW))
        do_sql(sql)
    else:
        retVal = {'stat':'failed', 'exam':ctgry, 'studentID':studentID}
    return HttpResponse(json.dumps(retVal), content_type="text/plain; charset=utf-8")


def removefromexamrec(request):
        courseCode = request.POST.get("classCode", "")
        studentID = request.POST.get("studentID", "")
        panel = request.POST.get("panel", "")
        sql = """
                DELETE FROM exam_rec WHERE id='{}' AND ctgry='{}'
            """.format(studentID, courseCode)
        do_sql(sql)

        nameSQL = do_sql(
            """
                SELECT firstname, lastname
                FROM id_rec
                WHERE id_rec.id = '{}'
            """.format( studentID)
        )
        stuName=""
        for name in nameSQL:
            stuName = name.firstname + " " + name.lastname
        courseNames = do_sql(
            """
                SELECT txt FROM exam_table WHERE exam = '{}'
            """.format(courseCode)
        )
        courseName=""
        for c in courseNames:
            courseName = c.txt

        retVal = {"studentName":stuName, "className":courseName, 'panel':panel}

        return HttpResponse(
            json.dumps(retVal), content_type="text/plain; charset=utf-8"
        )
