$(document).ready(function() {
    var studentIds = new Array();
    $( "#container").accordion({ active:false, header:'div.header', fillSpace:false, clearStyle:true, collapsible:true });

    // generate the list of placement exams from informix (displayed in the "Browse by placement exams" panel of the accordion)
    $.get('/exams/students/getcourses/', function(result) {
        $("#courseSelection p").after(result);
    });

    // execute searc for exam_rec data for one student by ID
    $("#onesearch").click(function() {loadSearchResults()});
});

function loadSearchResults() {
  console.log($("#student").val());
  $.post(
    '/exams/students/getstudentexams/',
    {
        'student': $("#student").val(),
        'csrfmiddlewaretoken': $csrfToken

    },
    //callback after search
    function(data, status){
      //place search result markup onto the page
      $("#studentSearchResuts").html(data).css({"margin-left": "300px"});
      //attach event handler to button for adding exam_rec for current student
      $("#addExamButton").click(function(){
        saveExam($("#selectedStudent1").val(), $("#selectedExam1").val(),"searchByStudent");
      });
      $(".examname input").click(function(){
        deleteExam($("#selectedStudent1").val(), $(this).next(":hidden").val(), "searchByStudent");
      });
    }
  );
}

function selectCourse(course,code) {
    //remove old form and clear the student ids
    $(".token-input-list").remove();
    studentIds = [];

    // UI stuff to indicate which exam has been selected
    $("#courseSelectionList > li").css({'font-weight':'normal', 'background-color':'transparent'});
    document.getElementById(code).style.fontWeight="bold";
    document.getElementById(code).style.backgroundColor="#ff9";
    course = course.replace("Placed in ", "");
    $("#studentSecTitle").text("Student list for: " + course);
    $("#studentInstructions").text("Add (by last name or Carthage ID)");

    // store the selected exam to a hidden field so it can later be passed along when saving a student-exam record
    $("#selectedExam").val(code);

    // display students with records for the selected exam
    $("#studentSelection p").show();
    $("#studentTextField").show();
    makeFieldPrepopulate(code);
}

function makeFieldPrepopulate(code) {
    //get the students credited with passing the selected exam
    $.ajax({
        url:'/exams/students/prepopulate/?q=' + code,
        type:'GET',
        dataType:"json",
        success: function(item) {
            $("#studentTextField").tokenInput('/exams/students/searchwithincourse/', {
                preventDuplicates:true,
                noResultsText:"Could not find student",
                searchingText:"Searching students...",
                hintText:"Search student last name or ID #",
                onAdd: function(item) {saveExam(item.id, $("#selectedExam").val(),"listByExam");},
                onDelete: function(item) {var index = studentIds.indexOf(item.id); studentIds.splice(index, 1); deleteExam(item.id, $("#selectedExam").val(),"listByExam");},
                prePopulate: item
            });
            $("#loadingImage").hide();
            //update styles depending on if there are any students in prepopulate
            $(".token-input-input-token").css({"border-bottom":"dotted", "border-width":"1px"});
            if(item.length < 1) {
                $(".token-input-input-token").css({"margin-bottom":"10px", "border-bottom":"none"});
            }
        }
    });
}

function saveExam(student, exam, panel) {
    $.ajax({
        type: 'POST',
        url:'/exams/students/addtoexamrec/',
        dataType: "json",
        data: {
            'csrfmiddlewaretoken': $csrfToken,
            'student': student,
            'courseCode': exam,
            'panel': panel
        },
        success: function(data) {
            var msg = data.stat == 'success' ? 'Exam record added for ' + data.studentID + ' (' + data.exam + ')' : 'Unable to add record for ' + data.studentID + '. Placement exam record already exists.';
            $('#notice').text(msg).show().delay(2000).fadeOut(function() {$(this).text('');});
            // depending on which panel we're working in, there are different UI/feedback steps
            if(data.panel == "listByExam" && data.stat != 'success'){
                // if the add fails in the botom panel, remove student from the list of students
                $('#studentTextField').tokenInput('remove', {id:data.studentID});
            }
            if(data.panel == "searchByStudent" && data.stat == 'success'){
                // after saving an exam, re-execute the search for this student to refresh the display
                loadSearchResults();
            }
        },
    });
}

function deleteExam(student, exam, panel) {
    //alert("student = " + student + "\nexam = " + exam + "\npanel = " + panel);
    $.ajax({
        type: 'POST',
        dataType:'json',
        url:'/exams/students/removefromexamrec/',
        data: {
            'csrfmiddlewaretoken': $csrfToken,
            'studentID': student,
            'classCode': exam,
            'panel': panel
        },
        success: function(data) {
            $("#notice").text(data.studentName + "'s exam was removed from \'" + data.className + "\'").show().delay(2000).fadeOut(function() {$(this).text('');});
            if(data.panel == "searchByStudent"){
                loadSearchResults();
            }
        }
    });
}
