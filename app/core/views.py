from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import (authenticate,login,logout)
from django.db.models import Q
import datetime
from datetime import timezone
from django.http import HttpResponse
from django.http import HttpResponseRedirect

from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token

from .models import *
from .serializers import *

import re

EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"


def idFormater(data, idToComplex=True):
    import datetime
    x = datetime.datetime.now()
    formater = 9713751690*x.year*x.month*x.day
    
    if idToComplex:
        formatedID = formater*int(data)
        return formatedID
    else:
        return int(int(data)/formater)


def sendingMail(users, tempFile, message=''):
    subject = 'RenYug Care'
    for user in users:
        html_message = render_to_string(tempFile, {'first_name': user.username, 'id': idFormater(user.id), 'message':message})
        plain_message = strip_tags(html_message)

        try:
            mail.send_mail(subject, plain_message, 'rentyuguser@gmail.com', [user.email], html_message=html_message)
            return True
        except:
            print("error in sending email.")
            return False


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sendVerifyEmail(request):
    user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
    failed = 0
    success = 0
    if user.is_superuser:
        subject = 'RenYug Email Verification'
        for user in Profile.objects.filter(emailConfirmed=False, emailNotification=True):
            html_message = render_to_string('verifyEmail.html', {'first_name': user.User.username, 'id': idFormater(user.User.id)})
            plain_message = strip_tags(html_message)
            try:
                mail.send_mail(subject, plain_message, 'rentyuguser@gmail.com', [user.User.email], html_message=html_message)
                success += 1
            except:
                failed += 1
        return Response({'msg':"Number of emails successfully sent : "+str(success)+" and Number of emails not sent : "+str(failed)})
    else:
        return Response({'error':"you are not a superuser."})
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sendGetProductEmail(request):
    user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
    failed = 0
    success = 0
    if user.is_superuser:
        subject = 'RenYug Beginner Mail'
        for user in Profile.objects.filter(emailNotification=True):
            html_message = render_to_string('getProductEmail.html', {'first_name': user.User.username})
            plain_message = strip_tags(html_message)
            try:
                mail.send_mail(subject, plain_message, 'rentyuguser@gmail.com', [user.User.email], html_message=html_message)
                success += 1
            except:
                failed += 1
        return Response({'msg':"Number of emails successfully sent : "+str(success)+" and Number of emails not sent : "+str(failed)})
    else:
        return Response({'error':"you are not a superuser."})
    
    

def sentMail(request, id):
    try:
        profile = Profile.objects.get(User__id=idFormater(id, False))
        profile.emailConfirmed = True
        profile.save()
        sendingMail([profile.User], 'confirmemail.html')
        return HttpResponseRedirect("https://rentyug.com")
    except:
        return HttpResponse("<h2> Sorry something is wrong, your mail is not on the way.<h2>")


def resetPass(request, id):
    try:
        profile = Profile.objects.get(User__id=idFormater(id, False))
        profile.User.set_password(str(id))
        profile.User.save()
        profile.emailConfirmed = True
        profile.save()
        return HttpResponseRedirect("https://rentyug.com/login")
    except:
        return HttpResponse("<h2> Sorry something is wrong.<h2>")



def fetchingMessages(username,msgMan):
    ''' this function filter the data and sort it acording to id.'''
    data1 = Messages.objects.filter(SendBy = username,
    RecievedBy = msgMan)
    
    data2 = Messages.objects.filter(SendBy = msgMan,
    RecievedBy = username)

    data = []

    i=0
    j=0
    while (i<len(data1) and j<len(data2)):
        if data1[i].id<data2[j].id:
            data.append(data1[i])
            i+=1
        else:
            data.append(data2[j])
            j+=1

    while i<len(data1):
        data.append(data1[i])
        i+=1

    while j<len(data2):
        data.append(data2[j])
        j+=1
    
    return data
        

@api_view(['POST'])
def mainPageData(request):
    if request.method=='POST':


        web_hits = TotalHits.objects.all()
        if web_hits.exists():
            web_hits = TotalHits.objects.all()[0]
            web_hits.Hits = int(web_hits.Hits)+1
            web_hits.save()
        else:
            web_hits = TotalHits.objects.create(Hits=1)

        
        data = {}
        data['ServiceCatagories']=ServicesCatagorySerializer(ServicesCatagory.objects.all(),
        many=True, context={'request':request}).data
        
        data['Plans']=PlansSerializer(Plans.objects.filter(Open=True),
        many=True, context={'request':request}).data
        
        data['FrontPageFeedback']=FrontPageFeedbackSerializer(FrontPageFeedback.objects.filter(Type='Good'),
        many=True, context={'request':request}).data

        if request.data['user'] is not None:
            
            dist_range = 2.0
            
            if Profile.objects.filter(User__username=request.data['user']).exists():
                profile = Profile.objects.get(User__username=request.data['user'])
                data['NearbyServices'] = ServiceSerializerForMainPage(
                    Service.objects.filter(lat__range = (profile.lat-dist_range,profile.lat+dist_range)).filter(lng__range = (profile.lng-dist_range,profile.lng+dist_range)),
                    many=True, context={'request':request}
                ).data

                data['UnreadMsg'] = MessageBox.objects.filter(Username=request.data['user'], UnreadMessages=True).count()

            if InterestedService.objects.filter(User__username=request.data['user']).exists():
                data['InterestedService']=InterestedServiceSerializer(InterestedService.objects.get(User__username=request.data['user']),
                        context={'request':request}).data
            else:
                data['InterestedService']={}

            web_hits_pppd = TotalHitsPerPersonPerDay.objects.get_or_create(Username=request.data['user'], Date=datetime.date.today())[0]
            web_hits_pppd.Hits = web_hits_pppd.Hits+1
            web_hits_pppd.save()
        else:
            data['InterestedService']={}
            data['NearbyServices']={}
        return Response(data)

@api_view(['GET'])
def getCategories(request):
    if request.method=='GET':
    
        data = {}
        data['ServiceCatagories']=ServicesCatagorySerializer(ServicesCatagory.objects.all(),
        many=True, context={'request':request}).data

        return Response(data)


@api_view(['GET'])
def getCategoryData(request, id):
    if request.method=='GET':
    
        data = {}
        data['categoryName'] = ServicesCatagory.objects.get(id=id).Name
        data['data']=ServiceSerializer(Service.objects.filter(Type__id=id),
        many=True, context={'request':request}).data

        return Response(data)



@api_view(['GET'])
def FAQData(request):
    if request.method=='GET':
    
        data = FAQSerializer(FAQ.objects.all(),many=True).data

        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def messageBox(request):
    if request.method=='POST':
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        data = MessageBox.objects.filter(Username = user.username)
        return Response(MessagesBoxSerializer(data, many=True, context={'request':request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def messages(request):
    if request.method=='POST':

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        
        updataData = MessageBox.objects.get(Username=user.username,
        MessagePartner=request.data['MessagePartner'])
        updataData.UnreadMessages=False
        updataData.save()

        data = {}

        data['messages'] = MessagesSerializer(fetchingMessages(user.username,request.data['MessagePartner']), many=True, context={'request':request}).data
        data['unreadMsg'] = MessageBox.objects.filter(Username=user.username, UnreadMessages=True).count()
        
        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addMessages(request):
    if request.method=='POST':
    
        dataToAdd = MessagesSerializer(data=request.data)
        if dataToAdd.is_valid():
            dataToAdd.create(dataToAdd.validated_data)
        
        data = fetchingMessages(request.data['SendBy'],request.data['RecievedBy'])

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user

        updataData = MessageBox.objects.get_or_create(Username=request.data['RecievedBy'],
        MessagePartner=request.data['SendBy'])[0]
        updataData.UnreadMessages=True
        updataData.save()

        updataData2 = MessageBox.objects.get_or_create(user.username,
        MessagePartner=request.data['RecievedBy'])[0]
        updataData2.save()

        profile = Profile.objects.get(User__username = request.data['RecievedBy'])

        if profile.emailConfirmed and profile.emailNotification:
            Recievers_last_messages = Messages.objects.filter(SendBy = request.data['RecievedBy'], RecievedBy = user.username)
            if Recievers_last_messages.exists():
                last_message_date = Recievers_last_messages.last().DateTime
                if(datetime.datetime.now(timezone.utc)-last_message_date).days>=1:

                    sendingMail([profile.User], 'newmsgemail.html',
                        message="You have Unread messages from "+str(user.username)+"."
                    )
            else:
                sendingMail([profile.User], 'newmsgemail.html',
                        message="You got messages first time from "+str(user.username)+"."
                )
        if profile.emailNotification:
            sendingMail([profile.User], 'signupemail.html')
        
        return Response(MessagesSerializer(data, many=True, context={'request':request}).data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addNewSmsBox(request):
    if request.method=='POST':
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        msg,created = MessageBox.objects.get_or_create(Username=user.username,
        MessagePartner=request.data['provider'])
        msg.UnreadMessages=False
        msg.save()

        msg2,created2 = MessageBox.objects.get_or_create(Username=request.data['provider'],
        MessagePartner=request.data['user'])
        msg2.UnreadMessages=True
        msg2.save()

        profile = Profile.objects.get(User__username = request.data['provider'])
        if profile.emailConfirmed and profile.emailNotification:
            sendingMail([profile.User], 'newmsgemail.html',
                message=str(user.username)+"Is trying to reach you for your product. Contact as soom as possible to get the deal."
            )

        return Response({'msg':'done'})


@api_view(['POST'])
def customLogin(request):
    email_or_username = request.data['username']
    if email_or_username and re.match(EMAIL_REGEX, email_or_username):
        users = User.objects.filter(email=email_or_username)
        if not users.exists():
            return Response({'error':'User with this email not found.'})
    else:
        users = User.objects.filter(username=email_or_username)
        if not users.exists():
            return Response({'error':'User with this username not found.'})
    user = users[0]
    if not user.check_password(request.data['password']):
        return Response({'error':'Password is incorrect.'})
    
    data = {'username':user.username}
    token, _  = Token.objects.get_or_create(user_id=user.id)
    data['token'] = token.key
    return Response(data)
    


@api_view(['POST'])
def signupAsProvider(request):
    if request.method=='POST':
        
        user_exist = User.objects.filter(username=request.data['username']).exists()
        if user_exist:
            return Response({'error':'USERNAME already exists.'})
        email = request.data['email']
        user_email_exist = User.objects.filter(email=email).exists()
        if user_email_exist:
            return Response({'error':'This EMAIL already exists.'})

        if email and not re.match(EMAIL_REGEX, email):
            return Response({'error':'EMAIL ID is not valid.'})

        

        user_data = UserSerializer(data=request.data)
        if user_data.is_valid(raise_exception=True):
            user = user_data.create(user_data.validated_data)

            user.set_password(request.data['password'])
            user.save()

            Profile_Image=Images.objects.create()
            Profile_Image.save()

            profile = Profile.objects.create(User=user,Image=Profile_Image)
            profile.save()

            user_ = authenticate(user_data.validated_data)
            if user_ is not None:
                user.last_login = datetime.datetime.now()
                user.save()
                login(request,user_)
            
            token, _  = Token.objects.get_or_create(user_id=user.id)
            if sendingMail([profile.User], 'signupemail.html'):
                return Response({"token": token.key})
            else:
                user_.delete()
                return Response({'error':'This email is corrupt or something is not good in our system.'})


@api_view(['POST'])
def forgotpass(request):
    data = {}
    if User.objects.filter(email=request.data['email']).exists():
        user = User.objects.get(email=request.data['email'])


        sendingMail([user], 'forgotpass.html',message='')

        data['msg'] = "Email sent"
    else:
        data['error'] = "Email not foundls."
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def logingout(request):
    if request.method=='GET':
        print('loging out!')
        return Response({'msg':'logout successfully.'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addFeedback(request):
    if request.method=='POST':
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        username = user.username
        msg = request.data['msg']

        profile = Profile.objects.get(User__username=username)
       
        new_feed = Feedbacks.objects.create(User=username,Message=msg,Image=profile.Image)
        front_feed = FrontPageFeedback.objects.create(Feedback=new_feed)
        
        new_feed.save()
        front_feed.save()
        
        data = {}
        data['FrontPageFeedback']=FrontPageFeedbackSerializer(FrontPageFeedback.objects.filter(Type='Good'),
        many=True, context={'request':request}).data

        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def account(request):
    if request.method=='POST':
        data={}
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id=user.id)
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
            
        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setFirstname(request):
    if request.method=='POST':
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user

        user.first_name = request.data['firstname']
        user.save()


        data={}
        
        profile = Profile.objects.get(User__username=user.username)
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                    
        
        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setLastname(request):
    if request.method=='POST':
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        user.last_name = request.data['lastname']
        user.save()
        data={}
        profile = Profile.objects.get(User__username=user.username)
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
        return Response(data)
        
 

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setEmail(request):
    if request.method=='POST':
        data={}
        email = request.data['email']
        if User.objects.filter(email=email).exists():
            data['error'] = "This email already exists. Use another one."
            return Response(data)
        if email and not re.match(EMAIL_REGEX, email):
            return Response({'error':'EMAIL ID is not valid.'})


        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__username=user.username)
        user.email = request.data['email']

        if sendingMail([user], 'signupemail.html'):
            user.save()
            
            profile.emailConfirmed = False
            data['profile'] = ProfileSerializer(profile, context={'request':request}).data
            profile.save()
        
            return Response(data)
        else:
            return Response({'error':'This email is corrupt or something is not good in our system.'})
        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def configEmail(request):
    if request.method=='POST':
        data={}

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__username=user.username)
        profile.save()
        sendingMail([user], 'signupemail.html')
        data['message'] = "Email sent for verification please verify."
        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setPassword(request):
    if request.method=='POST':
        
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user

        if user.check_password(request.data['oldPassword']):
            user.set_password(request.data['password'])
            user.save()
            data={}
            profile = Profile.objects.get(User__username=request.data['username'])
            data['profile'] = ProfileSerializer(profile, context={'request':request}).data

            return Response(data)
        else:
            return Response({'msg':'err'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setMyAddr(request):
    if request.method=='POST':
        data={}

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__username=user.username)
        profile.Address = request.data['Address']
        profile.save()
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
            
        return Response(data)
        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setLoc(request):
    if request.method=='POST':
        data={}

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__username=user.username)
        profile.lat = request.data['lat']
        profile.lng = request.data['lng']
        profile.save()
        data['msg'] = 'Location updated.'
        
        return Response(data)
   


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setMyNo(request):
    if request.method=='POST':
        data={}

        profile = Profile.objects.get(User__username=request.data['username'])
        profile.MobileNo = request.data['MobileNo']
        profile.save()
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data

        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setShopName(request):
    if request.method=='POST':

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        service = profile.Service.get(id=request.data['id'])

        service.ShopName = request.data['ShopName']
        service.VStatus = False
        service.save()

        data={}
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                    
        return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateShopCatagory(request):
    if request.method=='POST':

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        service = profile.Service.get(id=request.data['id'])

        serviceCatagory = ServicesCatagory.objects.get(id=request.data['catagoryId'])

        service.Type=serviceCatagory
        service.save()

        data={}
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)
        


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateMainImage(request):
    if request.method=='POST':
    
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        service = profile.Service.get(id=request.data['id'])

        service.MainImage = request.FILES.get('image')
        service.save()

        data={}
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)
        



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateImage(request):
    if request.method=='POST':
        
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        service = profile.Service.get(ServiceImages__id=request.data['id'])

        img = service.ServiceImages.get(id=request.data['id'])

        img.Image = request.FILES.get('image')
        img.save()

        data={}
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)
        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addNewImage(request):
    if request.method=='POST':
    
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        service = profile.Service.get(id=request.data['id'])

        img = Images.objects.create(Image=request.FILES.get('image'))

        service.ServiceImages.add(img)

        service.save()
        img.save()

        data = {}
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data

        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setOpenTime(request):
    if request.method=='POST':
    
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        service = profile.Service.get(id=request.data['id'])

        service.OpenTime = request.data['openTime']
        service.save()

        data={}
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)
        


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setCloseTime(request):
    if request.method=='POST':
    
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        service = profile.Service.get(id=request.data['id'])

        service.closeTime = request.data['closeTime']
        service.save()

        data={}
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)
        


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setRentalStatus(request):
    if request.method=='POST':
    
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        service = profile.Service.get(id=request.data['id'])

        service.RentalStatus = request.data['rentalStatus']
        service.save()

        data={}
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)
        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setGetNotification(request):
    if request.method=='POST':
        data={}
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        profile.emailNotification = request.data['getNotification']
        profile.save()
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
        print(request.data['getNotification'])
                            
        return Response(data)
        


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setNoOfItems(request):
    if request.method=='POST':
    
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        service = profile.Service.get(id=request.data['id'])

        service.NoOfItems = request.data['noOfItems']
        service.save()

        data={}
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)
        


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setPriceType(request):
    if request.method=='POST':
    
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        service = profile.Service.get(id=request.data['id'])

        service.PriceType = request.data['priceType']
        service.save()

        data={}
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateServiceAddr(request):
    if request.method=='POST':
    
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        service = profile.Service.get(id=request.data['id'])

        service.lat = request.data['lat']
        service.lng = request.data['lng']
        service.Address = request.data['Address']
        service.save()

        data={}
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deleteSearchName(request):
    if request.method=='POST':
        
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        service = profile.Service.get(SearchNames__id=request.data['id'])
        searchName = service.SearchNames.get(id=request.data['id'])
        searchName.delete()
        service.save()
        data={}
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deleteImage(request):
    if request.method=='POST':
        
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        service = profile.Service.get(ServiceImages__id=request.data['id'])
        img = service.ServiceImages.get(id=request.data['id'])
        img.delete()

        data={}
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addSearchName(request):
    if request.method=='POST':
        
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        service = profile.Service.get(id=request.data['serviceId'])

        searchName = SearchName.objects.create(Name=request.data['searchName'].upper())
        service.SearchNames.add(searchName)
        searchName.save()
        service.save()

        data={}
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data

        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addNewService(request):
    if request.method=='POST':

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)

        catagory = ServicesCatagory.objects.get(id=request.data['catagoryId'])
        
        service = Service.objects.create(
                MainImage=request.FILES.get('MainImage'),
                ShopName=request.data['ShopName'],
                Type=catagory,
                OpenTime=request.data['OpenTime'],
                Description=request.data['description'],
                closeTime=request.data['CloseTime'],
                PriceType=request.data['PriceType'],
                Address=profile.Address,
                lat=profile.lat,
                lng=profile.lng,
        )
        service.save()

        data={}
                
        
        profile.Service.add(service)
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
        profile.save()
                            
        return Response(data)

@api_view(['POST'])
def search(request):
    searchName = request.data['searchName'].upper()

    s_data = {}
    
    s_data['data'] = ServiceSerializer(Service.objects.filter(Q(SearchNames__Name=searchName) | Q(ShopName__icontains=searchName) | Q(Description__icontains=searchName)).distinct(), many=True, 
    context={'request':request}).data

    if request.data['Username'] is not None:
    
        profile = Profile.objects.get(User__username=request.data['Username'])

        lastSearchedTag = LastSearchedTag.objects.create(tag=searchName)
        profile.LastSearchedTags.add(lastSearchedTag)

        if Service.objects.filter(SearchNames__Name=searchName).exists():
            profile.LastSearcheTag = profile.LastSearcheTag + ',' + searchName
        else:
            profile.LastSearchNotFound = profile.LastSearchNotFound + ',' +searchName

        profile.save()

    return Response(s_data)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def productData(request):

    data={}
    service = Service.objects.get(id=request.data['productId'])
    data['data']=ServiceSerializer(service,
    context={'request':request}).data

    data['providerDetail']=ProfileSerializer(Profile.objects.get(
        Service__id=request.data['productId']
    ), context={'request':request}).data

    user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
    profile = Profile.objects.get(User__id = user.id)
    
    IService = InterestedService.objects.filter(User__username=request.data['Username']).exists()
    if IService:
        IService1 = InterestedService.objects.get(User__username=request.data['Username'])

    else:
        IService1 = InterestedService.objects.create(User=user)

    IService1.Services.add(service)
    IService1.save()

    for tag in service.SearchNames.all():
        profile.LastProductTags.add(tag)
        
    profile.LastCategory=service.Type
    profile.save()
     
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rentNow(request):
    data={}
    user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
    # profile = Profile.objects.get(User__id = user.id)
    # if(profile.User.first_name=='' or profile.User.last_name=='' or profile.MobileNo=='' or profile.Address==''):
    #     data['error'] = 'Profile is not completed. Please Complete your profile first.'
    # elif(profile.emailConfirmed is not True):
    #     data['error'] = 'Please verify your email first. This is neccessary for security reasons.'

    data['ContactNo'] = profile.MobileNo
    return Response(data)

    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rentNowConfirmed(request):
    data={}

    user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
    profile = Profile.objects.get(User__id = user.id)
    consumerNo = request.data["consumerContact"]
    providerProfile = Profile.objects.get(id=request.data['profileId'])
    product = Service.objects.get(id=request.data['productId'])

    html_message = render_to_string('bookinginfo.html', {

        'ConsumerUsername':profile.User.username,
        'ConsumerName':profile.User.first_name,
        'ConsumerMoNo':consumerNo,
        'providerUsername':providerProfile.User.username,
        'providerName':providerProfile.User.first_name,
        'providerMoNo':providerProfile.MobileNo,
        'productName':product.ShopName,
        'producRent':product.PriceType,

    })
    plain_message = strip_tags(html_message)
    subject = 'Bhai 5 min m call karna hai. Jaldi kar.'
    try:
        mail.send_mail(subject, plain_message, 'rentyuguser@gmail.com', ['sumitdhakad2232@gmail.com', 'ajaypatel3340@gmail.com'], html_message=html_message)
        data['msg'] = 'WE ARE CALLING IN 5 MINUTES.'
    except:
        data['msg'] = 'There is something wrong with the system. please try again in some time or directly contact the provider.'

    
    return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def giveRating(request):
    if request.method=='POST':

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)

        service_exist = Service.objects.filter(RatedBy__id=user.id).exists()

        if service_exist:
            return Response({'msg':'You have rated that.'})

        service = Service.objects.get(id=request.data['productId'])
        rating = (service.Rating +(int(request.data['rating']))/10)/2,1
        service.Rating = round(rating if rating<5 else 5)

        profile_rating = (profile.Rating + (int(request.data['rating']))/10)/2,1
        profile = Profile.objects.get(User__username=request.data['provider'])
        profile.Rating = round(profile_rating if profile_rating<5 else 5)
        profile.save()
        
        service.RatedBy.add(user)
        service.save()


        data={}
        data['data']=ServiceSerializer(Service.objects.get(id=request.data['productId']),
        context={'request':request}).data
        
        data['providerDetail']=ProfileSerializer(Profile.objects.get(
            Service__id=request.data['productId']
        ), context={'request':request}).data

        return Response(data)
        


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addServiceFeed(request):
    if request.method=='POST':


        feed = ServiceFeedback.objects.create(
            Username=request.data['user'],
            Message=request.data['feed']
        )

        service = Service.objects.get(id=request.data['productId'])

        service.ServiceFeedback.add(feed)
        service.save()
        feed.save()

        data={}
        data['data']=ServiceSerializer(Service.objects.get(id=request.data['productId']),
        context={'request':request}).data
                
        data['providerDetail']=ProfileSerializer(Profile.objects.get(
            Service__id=request.data['productId']
        ), context={'request':request}).data
        
        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateDesc(request):
    if request.method=='POST':

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)

        service = profile.Service.get(id=request.data['serviceId'])
        service.VStatus = False
        
        service.Description = request.data['desc']
        service.save()
        
        data={}
                        
        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                                    
        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def removeItem(request):
    if request.method=='POST':


        service = Service.objects.get(id=request.data['id'])
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user

        IService = InterestedService.objects.get(User__username=user.uername)

        IService.Services.remove(service)

        IService.save()

        data ={}

        data['InterestedService']=InterestedServiceSerializer(IService,
            context={'request':request}).data

        return Response(data)

def getPostData(Username, request, PostsStartId=0):

    if Username is not None:

        services = Service.objects.filter(Posts__Activated=True).exclude(Posts__LikedBy__username=Username).filter(id__gte=PostsStartId).order_by("-id").order_by('-Posts__TotalLikes')
        if len(services)>12:
            services = services[:10]
        elif len(services)<12:
            data=[]
        data = ServiceSerializerForPost(services,many=True, context={'request':request}).data
            
        return data

        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def posts(request):
    if request.method=='POST':
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        data = getPostData(user.username,request)

        return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def morePosts(request):
    if request.method=='POST':
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        data = getPostData(user.username,request,PostsStartId=request.data["PostsStartId"])

        return Response(data)

        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addPostComment(request):
    if request.method=='POST':

        post = Post.objects.get(id=request.data['postId'])
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user

        comment = PostComments.objects.create(Username=user.username,Comment=request.data['comment'])

        post.Comments.add(comment)
        comment.save()
        post.save()

        if request.data['type']=='myPost':
            profile = Profile.objects.get(User__id = user.id)
            services = profile.Service.all()
            data={}
            data['data'] = ServiceSerializerForPost(services, many=True, context={'request':request}).data

        else:
            data = PostCommentsSerializer(post.Comments, many=True, context={'request':request}).data

        return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def removePostComment(request):
    if request.method=='POST':
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        comment = PostComments.objects.get(id=request.data['commentId'],Username=user.username)
        comment.delete()

        if request.data['type']=='myPost':
            profile = Profile.objects.get(User__id = user.id)
            services = profile.Service.all()
            data={}
            data['data'] = ServiceSerializerForPost(services, many=True, context={'request':request}).data

        else:
            post = Post.objects.get(id=request.data['postId'])
            data = PostCommentsSerializer(post.Comments, many=True, context={'request':request}).data


        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addPostCommentReply(request):
    if request.method=='POST':
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        comment = PostComments.objects.get(id=request.data['commentId'])
        reply = PostCommentsReplies.objects.create(Username=user.username,Reply=request.data['reply'])

        comment.Replies.add(reply)
        reply.save()
        comment.save()


        if request.data['type']=='myPost':
            profile = Profile.objects.get(User__username=user.username)
            services = profile.Service.all()
            data={}
            data['data'] = ServiceSerializerForPost(services, many=True, context={'request':request}).data

        else:
            post = Post.objects.get(id=request.data['postId'])
            data = PostCommentsSerializer(post.Comments, many=True, context={'request':request}).data


        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def removePostCommentReply(request):
    if request.method=='POST':

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)

        reply = PostCommentsReplies.objects.get(id=request.data['replyId'], Username=user.username)
        reply.delete()

        if request.data['type']=='myPost':
            profile = Profile.objects.get(User__username=user.username)
            services = profile.Service.all()
            data={}
            data['data'] = ServiceSerializerForPost(services, many=True, context={'request':request}).data

        else:
            post = Post.objects.get(id=request.data['postId'])
            data = PostCommentsSerializer(post.Comments, many=True, context={'request':request}).data

        return Response(data)


        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addPostLike(request):
    if request.method=='POST':

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        post = Post.objects.get(id=request.data['postId'])

        if post.LikedBy.filter(id=user.id).exists():
            post.TotalLikes = int(post.TotalLikes)-1
            post.LikedBy.remove(user)
        else:
            post.TotalLikes = int(post.TotalLikes)+1
            post.LikedBy.add(user)
        post.save()

        if request.data['type']=='myPost':
            services = profile.Service.all()
            data={}
            data['data'] = ServiceSerializerForPost(services, many=True, context={'request':request}).data
        else:
            data = {}
            data['LikedBy'] = UserSerializer(post.LikedBy, many=True, context={'request':request}).data
            data['TotalLikes'] = post.TotalLikes
        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def savePost(request):
    if request.method=='POST':

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)

        service = Service.objects.get(id=request.data['serviceId'])

        if profile.SavedServices.filter(id=service.id).exists():
            profile.SavedServices.remove(service)
            profile.save()
            return Response({'msg':'Service removed'})
        else:
            profile.SavedServices.add(service)
            profile.save()
            return Response({'msg':'Service saved'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def myPosts(request):
    if request.method=='POST':

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        services = profile.Service.all()
        data = ServiceSerializerForPost(services, many=True, context={'request':request}).data
        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activatePostTogle(request):
    if request.method=='POST':

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        post = profile.Service.get(Posts__id=request.data["postId"]).Posts(id=request.data["postId"])

        if post.Activated:
            post.Activated = False
        else:
            post.Activated = True
        post.save()

        services = profile.Service.all()
        data = ServiceSerializer(services, many=True, context={'request':request}).data
            
        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addNewPost(request):
    if request.method=='POST':
        
        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        service = profile.Service.get(id=request.data['selectedServiceId'])

        if service.Posts.count()>3:
            return Response({'msg':'You cannot add more than 3 posts per service.'})

        if request.data['hasImage']=='true':
            hasImage=True
        else:hasImage= False


        post = Post.objects.create(
                        Tittle=request.data['Tittle'],
                        HasImage=hasImage,
                        Image=request.FILES.get('Image'),
                        Media=request.FILES.get('Media'),
                        Text=request.data['Text']
                )

        service.Posts.add(post)
        post.save()
        service.save()

        services = profile.Service.all()
        data = ServiceSerializerForPost(services, many=True, context={'request':request}).data
        return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def savedServices(request):
    if request.method=='POST':

        user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
        profile = Profile.objects.get(User__id = user.id)
        
        data={}
        data['data']=ServiceSerializerForMainPage(profile.SavedServices.all(), many=True, 
                context={'request':request}).data

        return Response(data)



@api_view(['GET'])
def requestedServices(request):
        
    data={}
    data['data']=RequestedServiceSerializer(RequestedService.objects.filter(completed=False), many=True, 
            context={'request':request}).data
    return Response(data)


@api_view(['POST'])
def completedRequestService(request):
    data={}
    user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user

    toComplete = RequestedService.objects.get(id=request.data['id'], User__id=user.id)
    toComplete.completed=True
    toComplete.save()

    data['msg']='Successfull'
    return Response(data)


@api_view(['POST'])
def addingServiceRequest(request):
    user = Token.objects.get(key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]).user
    newData = RequestedService.objects.create(
        User = user,
        Title = request.data['title'],
        Description = request.data['description'],
        ContactInfo = request.data['contactInfo']
    )
    newData.save()
    data={}
    data['data']=RequestedServiceSerializer(RequestedService.objects.filter(completed=False), many=True, 
            context={'request':request}).data
    return Response(data)