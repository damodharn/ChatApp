import re
from django.core.validators import validate_email, ValidationError, RegexValidator, EmailValidator
import os
from .models import ChatUser
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
import jwt
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMessage
from django.conf import settings


@csrf_exempt
def reg(request):
    return render(request, 'chat/register.html', {})


@csrf_exempt
def login_view(request):
    return render(request, 'chat/login.html', {})


@csrf_exempt
def frgtvw(request):
    return render(request, 'chat/forget.html', {})


@csrf_exempt
def login(request):
    print("Here in Login")
    try:
        if request.method == "POST":
            # check if a user exists
            # with the username and password
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if not user:
                raise ObjectDoesNotExist("Wrong Username/Password combination or register before login.")
            if user is not None and user.is_active is True:
                return render(request, 'chat/open_chat.html', {
                    'message': "You are Logged In Successfully...!"
                })
            else:
                if user.is_active is False:
                    return render(request, 'chat/display.html', {
                        'message': "Please verify your email by clicking link sent to your mail-id."
                    })
        else:
            return render(request, 'chat/display.html', {
                'message': "Invalid request"
            })
    except ObjectDoesNotExist as e:
        return render(request, 'chat/display.html', {
            'message': str(e)
        })


@csrf_exempt
def signup(request):
    if request.method == "POST":
        if request.POST['password'] == request.POST['password2']:
            '''if both the passwords matched.
            check if a user already  exists.'''
            # try:
            username = request.POST['username']
            x = re.search("\s", username)
            if (len(username) < 4) or x:  # Validating username
                return HttpResponse("enter valid username; with at least 4 char and no whitespace")
            email = request.POST['email']
            try:
                validate_email(email)  # Validating email id
            except ValidationError as e:
                return HttpResponse(str(e))
            ''' Checking if user with
             this username and email is already present or not.'''
            try:
                user = User.objects.get(username=request.POST['username'])
                if user:
                    return render(request, 'chat/display.html', {
                        'message': 'Username already been there.'
                                   '...try with different username'
                    })
            except ObjectDoesNotExist:
                try:
                    user1 = User.objects.get(email=request.POST['email'])
                    if user1:
                        return render(request, 'chat/display.html', {
                            'message': 'Email-id has already been taken.'
                        })
                except ObjectDoesNotExist:
                    '''If User doesn't exist 
                                    Create a new User.'''
                    user = User.objects.create_user(username=request.POST['username'], password=request.POST['password']
                                                    ,
                                                    first_name=request.POST['first_name'],
                                                    last_name=request.POST['last_name'], email=request.POST['email'])
                    user.is_active = False  # making is_active false until the email is verified.
                    user.save()
                    '''Generating jwt token.'''
                    # creating payload
                    payload = {
                        'uid': user.id,
                        'email': user.email,
                        'username': user.username
                    }
                    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256').decode('utf-8')  # encoding jwt token
                    current_site = get_current_site(request)
                    mail_subject = 'Activate your account by clicking below link.'
                    message = render_to_string('chat/account_active_email.html', {
                        'user': user.username,
                        'domain': current_site.domain,
                        'token': token
                    }
                                               )
                    to_email = user.email
                    email = EmailMessage(
                        mail_subject, message, to=[to_email]
                    )
                    email.send()
                    return render(request, 'chat/display.html', {
                        'message': 'Successfully Registered !!'
                                   'Now confirm your email to activate an account'
                    })
        else:
            return render(request, 'chat/display.html', {
                'message': "Password does not matched. "
            })
    else:
        return HttpResponse('Error: Invalid Request(GET).')


@csrf_exempt
def activate(request, token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithm='HS256')  # .decode('utf-8')
        uid = payload['uid']  # getting the user id from the payload
        user = User.objects.get(id=uid)  # getting the user through the id
        if not user:
            raise ObjectDoesNotExist("User Does Not Exist..")
        user.is_active = True  # making user is_active to true for login purposes
        user.save()  # saving the user
        return HttpResponse('Registration successful !\nNow you can login to your account.')
    except Exception as e:
        return HttpResponse(str(e))


@csrf_exempt
def delete(request):
    try:
        email = request.POST['email']
        User.objects.filter(email=email).delete()
        return HttpResponse('Deletion completed successfully')
    except ObjectDoesNotExist:
        return HttpResponse('User with this email not found')


@csrf_exempt
def forget(request):
    try:
        # username = request.POST["username"]
        email = request.POST["email"]  # getting the email from the request
        password = request.POST['password']
        password2 = request.POST['password2']
        if password == password2:
            user = User.objects.get(email=email)
            if not user:
                raise ObjectDoesNotExist('User does not exist.')
            if user:
                current_site = get_current_site(request)  # getting the domain
                payload = {
                    'email': user.email,  # generating the payload
                    'password': password
                }

                mail_subject = "Forgot password"  # mail subject
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256').decode('utf-8')  # generating the token
                message = render_to_string('chat/forget_password.html', {
                    'user': user.username,
                    "domain": current_site,
                    "token": token
                })
                email = EmailMessage(mail_subject, message, to=[email])  # generating the email using EmailMessage class
                email.send()  # sending the email
                return HttpResponse("Please click the link given in your mail to Reset new password.")
            else:
                return HttpResponse('Invalid Email id')
        else:
            return HttpResponse('Password does not matched')
    except (ValueError, ObjectDoesNotExist) as e:
        return HttpResponse(str(e))


@csrf_exempt
def reset(request, token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithm='HS256')
        email = payload['email']
        password = password2 = payload['password']
        if password == password2:
            user = User.objects.get(email=email)
            if user:
                user.Password = password
                user.save()
                return HttpResponse('Password Reset Successfully Done !')
            else:
                return HttpResponse('Wrong entry: Email not found')
        else:
            return HttpResponse('Passwords not Matching')
    except (ObjectDoesNotExist, ValueError) as e:
        return HttpResponse(str(e))