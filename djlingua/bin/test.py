from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from djzbar.utils.informix import do_sql

import datetime
import json

studentIds = '[{"studentID":""},{"studentID":""}]'
ctgry = "S102"
ctgry = ctgry[:1]

adds=[]
objs = json.loads(studentIds)
NOW = str(datetime.datetime.now().strftime("%m/%d/%Y"))
for student in objs:
    print student['studentID']

    sql = """
        SELECT * FROM exam_rec WHERE id = '{}' AND ctgry LIKE '{}%%'
    """.format(student['studentID'], ctgry)

    duplicates = do_sql(sql)
    numRows=0;

    #print duplicates.rowcount

    for d in duplicates:
        #numRows = d.numRows
        numRows=numRows+1
    print numRows

