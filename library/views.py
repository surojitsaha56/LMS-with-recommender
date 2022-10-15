from multiprocessing.sharedctypes import Value
from sre_constants import SUCCESS
from django.shortcuts import render, HttpResponse
from django.http import HttpResponseRedirect
from . import forms,models
from django.http import HttpResponseRedirect
from django.contrib.auth.models import Group
from django.contrib import auth
from django.contrib.auth.decorators import login_required,user_passes_test
from datetime import datetime,timedelta,date
from django.core.mail import send_mail
from librarymanagement.settings import EMAIL_HOST_USER
from django.contrib import messages
import xlwt
import datetime
from django.contrib.auth.models import User
from twilio.rest import Client
from decouple import config


def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'library/index.html')

#for showing signup/login button for student
def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'library/studentclick.html')

#for showing signup/login button for teacher
def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'library/adminclick.html')



def adminsignup_view(request):
    form=forms.AdminSigupForm()
    if request.method=='POST':
        form=forms.AdminSigupForm(request.POST)
        if form.is_valid():
            user=form.save()
            user.set_password(user.password)
            user.save()


            my_admin_group = Group.objects.get_or_create(name='ADMIN')
            my_admin_group[0].user_set.add(user)

            return HttpResponseRedirect('adminlogin')
    return render(request,'library/adminsignup.html',{'form':form})






def studentsignup_view(request):
    form1=forms.StudentUserForm()
    form2=forms.StudentExtraForm()
    mydict={'form1':form1,'form2':form2}
    if request.method=='POST':
        form1=forms.StudentUserForm(request.POST)
        form2=forms.StudentExtraForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            user=form1.save()
            user.set_password(user.password)
            user.save()
            f2=form2.save(commit=False)
            print('StudentExtra created')
            f2.user=user
            f2.save()
            print('Student Extra final saved')

            my_student_group = Group.objects.get_or_create(name='STUDENT')
            my_student_group[0].user_set.add(user)

        return HttpResponseRedirect('studentlogin')
    return render(request,'library/studentsignup.html',context=mydict)




def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()

def afterlogin_view(request):
    if is_admin(request.user):
        return render(request,'library/adminafterlogin.html')
    else:
        return render(request,'library/studentafterlogin.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def addbook_view(request):
    #now it is empty book form for sending to html
    form=forms.BookForm()
    if request.method=='POST':
        #now this form have data from html
        form=forms.BookForm(request.POST)
        if form.is_valid():
            user=form.save()
            return render(request,'library/bookadded.html')
    return render(request,'library/addbook.html',{'form':form})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewbook_view(request):
    books=models.Book.objects.all()
    return render(request,'library/viewbook.html',{'books':books})




@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def issuebook_view(request):
    form=forms.IssuedBookForm()
    if request.method=='POST':
        #now this form have data from html
        form=forms.IssuedBookForm(request.POST)
        if form.is_valid():
            obj=models.IssuedBook()
            obj.enrollment=request.POST.get('enrollment2')
            print(request.POST.get('enrollment2'))
            obj.isbn=request.POST.get('isbn2')

            bookcount = models.Book.objects.filter(isbn=obj.isbn)[0].count

            # if models.IssuedBook.objects.filter(isbn=obj.isbn).exists():
            #     print('bruh')
            #     messages.success(request, 'Please enter details correctly')

            if bookcount == 0:
                print('Hi')
                messages.info(request, 'Book not availabe')
                return render(request,'library/issuebook.html',{'form':form})

            else:
                student = models.StudentExtra.objects.filter(enrollment=request.POST.get('enrollment2'))[0]
                bookname = models.Book.objects.filter(isbn = obj.isbn)[0]
                expiry_date = date.today() + timedelta(days=15)
                phone = '+91'+student.phone
                print(phone)
                
                bookcount -= 1
                book = models.Book.objects.filter(isbn=obj.isbn).update(count = bookcount)
            
                account_sid = config('account_sid')
                auth_token = config('auth_token')
                client = Client(account_sid, auth_token)

                message = client.messages \
                                .create(
                                        body='You have issued' + str(bookname) + 'Expiry date is: ' + str(expiry_date),
                                        from_='+17472985342',
                                        to=phone
                                    )

                print(message.sid)
                messages.success(request, 'Issued Book')
                obj.save()

                

                    

            return render(request,'library/bookissued.html')

           
    return render(request,'library/issuebook.html',{'form':form})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewissuedbook_view(request):
    issuedbooks=models.IssuedBook.objects.all()
    li=[]
    for ib in issuedbooks:
        issdate=str(ib.issuedate.day)+'-'+str(ib.issuedate.month)+'-'+str(ib.issuedate.year)
        expdate=str(ib.expirydate.day)+'-'+str(ib.expirydate.month)+'-'+str(ib.expirydate.year)
        #fine calculation
        days=(date.today()-ib.issuedate)
        # print(date.today())
        d=days.days
        fine=0
        if d>15:
            day=d-15
            fine=day*10


        books=list(models.Book.objects.filter(isbn=ib.isbn))
        students=list(models.StudentExtra.objects.filter(enrollment=ib.enrollment))
        i=0
        for l in books:
            t=(students[i].get_name,students[i].enrollment,books[i].name,books[i].author,issdate,expdate,fine)
            i=i+1
            li.append(t)

    return render(request,'library/viewissuedbook.html',{'li':li})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewstudent_view(request):
    students=models.StudentExtra.objects.all()
    return render(request,'library/viewstudent.html',{'students':students})


@login_required(login_url='studentlogin')
def viewissuedbookbystudent(request):
    student=models.StudentExtra.objects.filter(user_id=request.user.id)
    issuedbook=models.IssuedBook.objects.filter(enrollment=student[0].enrollment)

    li1=[]

    li2=[]
    for ib in issuedbook:
        books=models.Book.objects.filter(isbn=ib.isbn)
        for book in books:
            t=(request.user,student[0].enrollment,student[0].branch,book.name,book.author)
            li1.append(t)
            
        print(li1)
    
        issdate=str(ib.issuedate.day)+'-'+str(ib.issuedate.month)+'-'+str(ib.issuedate.year)
        expdate=str(ib.expirydate.day)+'-'+str(ib.expirydate.month)+'-'+str(ib.expirydate.year)
        #fine calculation
        days=(date.today()-ib.issuedate)
        print(date.today())
        d=days.days
        fine=0
        if d>15:
            day=d-15
            fine=day*10
        t=(issdate,expdate,fine)
        li2.append(t)

    return render(request,'library/viewissuedbookbystudent.html',{'li1':li1,'li2':li2})

def aboutus_view(request):
    return render(request,'library/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message, EMAIL_HOST_USER, ['wapka1503@gmail.com'], fail_silently = False)
            return render(request, 'library/contactussuccess.html')
    return render(request, 'library/contactus.html', {'form':sub})

@login_required(login_url='studentlogin')
def searchBook_view(request):
    if request.method == "POST":
        query_name = request.POST.get('name', None)
        if query_name:
            results = models.Book.objects.filter(name__contains=query_name)
            return render(request, 'library/search.html', {"results":results})

    # return render(request, 'product-search.html')

def exportExcelBook(request):
    response=HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition']='attachment; filename=Books'+ \
        str(datetime.datetime.now())+'.xls'
    wb=xlwt.Workbook(encoding='utf-8')
    ws=wb.add_sheet('Books')
    row_num=0
    font_style=xlwt.XFStyle()
    font_style.font.bold=True
    columns=['Book Name', 'ISBN', 'Author', 'Category']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    font_style=xlwt.XFStyle()

    rows=models.Book.objects.all().values_list('name', 'isbn', 'author', 'category')

    for row in rows:
        row_num+=1

        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)
    wb.save(response)

    return response


def exportExcelStudents(request):
    response=HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition']='attachment; filename=Students'+ \
        str(datetime.datetime.now())+'.xls'
    wb=xlwt.Workbook(encoding='utf-8')
    ws=wb.add_sheet('Students')
    row_num=0
    font_style=xlwt.XFStyle()
    font_style.font.bold=True
    columns=['Full Name', 'Enrollment', 'Branch']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    font_style=xlwt.XFStyle()

    rows1=models.StudentExtra.objects.all().values_list('fullname', 'enrollment', 'branch')

    for row in rows1:
        row_num+=1

        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)
    wb.save(response)

    return response

def recommenderSystem(bookname):
    print('in')
    booknamelist = bookname.split(' ')
    results = []
    for word in booknamelist:
        books = models.Book.objects.filter(name__contains=word)
        books = list(books)
        for book in books:
            print(book)
            if book.name not in results and book.name != bookname:
                results.append(book.name)
    return results






























@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def returnBook(request):
    form=forms.ReturnBookForm()

    if request.method=='POST':
        studentid2=request.POST.get('enrollment3')
        bookid2=request.POST.get('isbn3')
        ratings=request.POST.get('rating')
        r1=int(models.Book.objects.get(isbn=bookid2).rating)
        r=(((int(ratings)+r1)//2)%10)
    
        book=models.Book.objects.filter(isbn=bookid2).update(rating=r)
        
        # print(book)

        if models.IssuedBook.objects.filter(enrollment=studentid2).exists() and models.IssuedBook.objects.filter(isbn=bookid2).exists():

            form=forms.ReturnBookForm(request.POST)
            if form.is_valid():

                tuple2delete=models.IssuedBook.objects.get(enrollment=studentid2, isbn=bookid2)
                bookname=models.Book.objects.filter(isbn=bookid2)[0]

                # Updating the count of the book while returning
                bookcount = models.Book.objects.filter(isbn=bookid2)[0].count
                bookcount += 1
                models.Book.objects.filter(isbn=bookid2).update(count = bookcount)

                print('start')
                recommended_books = recommenderSystem(bookname.name)
                print(str(recommended_books))


                #delete entry from issuetable
                tuple2delete.delete()

                student = models.StudentExtra.objects.filter(enrollment = studentid2)[0]
                bookname = models.Book.objects.filter(isbn = bookid2)[0]
                phone = '+91'+student.phone
                print(phone)
            
                account_sid = config('account_sid')
                auth_token = config('auth_token')
                client = Client(account_sid, auth_token)

                message = client.messages \
                                .create(
                                        body='Recommended books:' + str(recommended_books),
                                        from_='+17472985342',
                                        to=phone
                                    )

                print(message.sid)

                messages.success(request, 'Book returned')
    context={'form': form}
    return render(request, 'library/returnbook.html', context)


