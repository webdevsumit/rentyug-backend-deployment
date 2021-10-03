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
        except:
            print("error in sending email.")

    

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


                unreadMsg = MessageBox.objects.filter(Username=request.data['user'], UnreadMessages=True)
                if unreadMsg.exists():
                    data['UnreadMsg'] = unreadMsg.count()

                
            


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
        data = MessageBox.objects.filter(Username = request.data['Username'])
        return Response(MessagesBoxSerializer(data, many=True, context={'request':request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def messages(request):
    if request.method=='POST':
        
        updataData = MessageBox.objects.get(Username=request.data['Username'],
        MessagePartner=request.data['MessagePartner'])
        updataData.UnreadMessages=False
        updataData.save()


        data = fetchingMessages(request.data['Username'],request.data['MessagePartner'])
        
        return Response(MessagesSerializer(data, many=True, context={'request':request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addMessages(request):
    if request.method=='POST':
    
        dataToAdd = MessagesSerializer(data=request.data)
        if dataToAdd.is_valid():
            dataToAdd.create(dataToAdd.validated_data)
        
        data = fetchingMessages(request.data['SendBy'],request.data['RecievedBy'])

        updataData = MessageBox.objects.get(Username=request.data['RecievedBy'],
        MessagePartner=request.data['SendBy'])
        updataData.UnreadMessages=True
        updataData.save()

        profile = Profile.objects.get(User__username = request.data['RecievedBy'])

        if profile.emailConfirmed and profile.emailNotification:
            Recievers_last_messages = Messages.objects.filter(SendBy = request.data['RecievedBy'], RecievedBy = request.data['SendBy'])
            if Recievers_last_messages.exists():
                last_message_date = Recievers_last_messages.last().DateTime
                if(datetime.datetime.now(timezone.utc)-last_message_date).days>=1:

                    sendingMail([profile.User], 'newmsgemail.html',
                        message="You have Unread messages from "+str(request.data['SendBy'])+"."
                    )
            else:
                sendingMail([profile.User], 'newmsgemail.html',
                        message="You got messages first time from "+str(request.data['SendBy'])+"."
                )
        
        return Response(MessagesSerializer(data, many=True, context={'request':request}).data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addNewSmsBox(request):
    if request.method=='POST':
    
        msg,created = MessageBox.objects.get_or_create(Username=request.data['user'],
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
                message=str(request.data['user'])+"Is trying to reach you for your product. Contact as soom as possible to get the deal."
            )

        return Response({'msg':'done'})


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
    if User.objects.filter(username=request.data['username']).exists():
        user = User.objects.get(username=request.data['username'])

        sendingMail([user], 'forgotpass.html',message='')

        data['msg'] = "Email sent"
    else:
        data['error'] = "Username is not valid."
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def logout(request):
    if request.method=='GET':
        print('loging out!')
        return Response({'msg':'logout successfully.'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addFeedback(request):
    if request.method=='POST':
        username = request.data['username']
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

        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
            
        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setFirstname(request):
    if request.method=='POST':
        user = User.objects.get(username=request.data['username'])


        user.first_name = request.data['firstname']
        user.save()


        data={}
        
        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                    
        
        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setLastname(request):
    if request.method=='POST':
        user = User.objects.get(username=request.data['username'])


        user.last_name = request.data['lastname']
        user.save()


        data={}
        
        profile = Profile.objects.get(User__username=request.data['username'])
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
        user = User.objects.get(username=request.data['username'])

        user.email = request.data['email']
        user.save()

        
        profile = Profile.objects.get(User__username=request.data['username'])
        profile.emailConfirmed = False
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
        profile.save()
        sendingMail([profile.User], 'signupemail.html')
        return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def configEmail(request):
    if request.method=='POST':
        data={}

        profile = Profile.objects.get(User__username=request.data['username'])
        profile.save()
        sendingMail([profile.User], 'signupemail.html')
        data['message'] = "Email sent for verification please verify."
        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setPassword(request):
    if request.method=='POST':
    
        user = authenticate(username=request.data['username'], password=request.data['oldPassword'])

        if user is not None:
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

        profile = Profile.objects.get(User__username=request.data['username'])
        profile.Address = request.data['Address']
        profile.save()
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
            
        
        return Response(data)
        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setLoc(request):
    if request.method=='POST':
        data={}

        profile = Profile.objects.get(User__username=request.data['username'])
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
        service = Service.objects.get(id=request.data['id'])


        service.ShopName = request.data['ShopName']
        service.VStatus = False
        service.save()


        data={}
        
        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                    
        return Response(data)
        
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ShopCatagories(request):
    if request.method=='GET':

        data = {}
        data['data']=ServicesCatagorySerializer(ServicesCatagory.objects.all(), 
        many=True,context={'request':request}).data

        return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateShopCatagory(request):
    if request.method=='POST':
        service = Service.objects.get(id=request.data['serviceId'])
        service.VStatus = False

        serviceCatagory = ServicesCatagory.objects.get(id=request.data['catagoryId'])

        service.Type=serviceCatagory
        service.save()

        data={}
                
        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)
        


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateMainImage(request):
    if request.method=='POST':
    
        service = Service.objects.get(id=request.data['id'])

        service.MainImage = request.FILES.get('image')
        service.save()

        data={}
                
        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)
        



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateImage(request):
    if request.method=='POST':
    
        img = Images.objects.get(id=request.data['id'])

        img.Image = request.FILES.get('image')
        img.save()

        data={}
                
        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)
        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addNewImage(request):
    if request.method=='POST':
    
        service = Service.objects.get(id=request.data['id'])

        img = Images.objects.create(Image=request.FILES.get('image'))

        service.ServiceImages.add(img)

        service.save()
        img.save()


        data = {}

        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data

        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setOpenTime(request):
    if request.method=='POST':
    
        service = Service.objects.get(id=request.data['id'])

        service.OpenTime = request.data['openTime']
        service.save()

        data={}
                
        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)
        


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setCloseTime(request):
    if request.method=='POST':
    
        service = Service.objects.get(id=request.data['id'])

        service.closeTime = request.data['closeTime']
        service.save()

        data={}
                
        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)
        


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setRentalStatus(request):
    if request.method=='POST':
    
        service = Service.objects.get(id=request.data['id'])

        service.RentalStatus = request.data['rentalStatus']
        service.save()

        data={}
                
        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)
        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setGetNotification(request):
    if request.method=='POST':
        data={}
                
        profile = Profile.objects.get(User__username=request.data['username'])
        profile.emailNotification = request.data['getNotification']
        profile.save()
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
        print(request.data['getNotification'])
                            
        return Response(data)
        


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setNoOfItems(request):
    if request.method=='POST':
    
        service = Service.objects.get(id=request.data['id'])

        service.NoOfItems = request.data['noOfItems']
        service.save()

        data={}
                
        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)
        


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setPriceType(request):
    if request.method=='POST':
    
        service = Service.objects.get(id=request.data['id'])

        service.PriceType = request.data['priceType']
        service.save()

        data={}
                
        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateServiceAddr(request):
    if request.method=='POST':
    
        service = Service.objects.get(id = request.data['id'])

        service.lat = request.data['lat']
        service.lng = request.data['lng']
        service.Address = request.data['Address']
        service.save()

        data={}
                
        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deleteSearchName(request):
    if request.method=='POST':
    
        searchName = SearchName.objects.get(id=request.data['id'])
        searchName.delete()

        data={}
            
        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
                            
        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deleteImage(request):
    if request.method=='POST':
    
        img = Images.objects.get(id=request.data['id'])
        img.delete()

        data={}
                
        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data
        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addSearchName(request):
    if request.method=='POST':
    
        searchName = SearchName.objects.create(Name=request.data['searchName'].upper())
        service = Service.objects.get(id=request.data['serviceId'])
        service.SearchNames.add(searchName)
        searchName.save()
        service.save()

        data={}
                
        profile = Profile.objects.get(User__username=request.data['username'])
        data['profile'] = ProfileSerializer(profile, context={'request':request}).data

        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addNewService(request):
    if request.method=='POST':


        profile = Profile.objects.get(User__username=request.data['username'])
        catagory = ServicesCatagory.objects.get(id=request.data['catagoryId'])
        
        service = Service.objects.create(
                MainImage=request.FILES.get('MainImage'),
                ShopName=request.data['ShopName'],
                Type=catagory,
                OpenTime=request.data['OpenTime'],
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
            profile.LastSearcheTag = searchName
        else:
            profile.LastSearchNotFound = searchName

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

    user = User.objects.get(username=request.data['Username'])
    
    IService = InterestedService.objects.filter(User__username=request.data['Username']).exists()
    if IService:
        IService1 = InterestedService.objects.get(User__username=request.data['Username'])

    else:
        IService1 = InterestedService.objects.create(User=user)

    IService1.Services.add(service)
    IService1.save()


    profile = Profile.objects.get(User__username=request.data['Username'])

    for tag in service.SearchNames.all():
        profile.LastProductTags.add(tag)
        
    profile.LastCategory=service.Type
    profile.save()
     
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rentNow(request):
    data={}

    profile = Profile.objects.get(User__username=request.data['username'])
    if(profile.User.first_name=='' or profile.User.last_name=='' or profile.MobileNo=='' or profile.Address==''):
        data['error'] = 'Profile is not completed. Please Complete your profile first.'
    elif(profile.emailConfirmed is not True):
        data['error'] = 'Please verify your email first. This is neccessary for security reasons.'
    else:
        data['ContactNo'] = profile.MobileNo
    return Response(data)

    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rentNowConfirmed(request):
    data={}

    profile = Profile.objects.get(User__username=request.data['username'])
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

        service_exist = Service.objects.filter(RatedBy__username=request.data['user']).exists()

        if service_exist:
            return Response({'msg':'You have rated that.'})

        service = Service.objects.get(id=request.data['productId'])
        user = User.objects.get(username=request.data['user'])

        service.Rating = round(( service.Rating + (int(request.data['rating']))/10)/2,1)

        profile = Profile.objects.get(User__username=request.data['provider'])
        profile.Rating = round(( profile.Rating + (int(request.data['rating']))/10)/2,1)
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


        service = Service.objects.get(id=request.data['serviceId'])
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

        IService = InterestedService.objects.get(User__username=request.data['user'])

        IService.Services.remove(service)

        IService.save()

        data ={}

        data['InterestedService']=InterestedServiceSerializer(IService,
            context={'request':request}).data

        return Response(data)

def getPostData(Username,request):

    if Username is not None:

        data = {}
        data['data'] = []

        profile = Profile.objects.get(User__username=Username)
        
        service_tags = profile.LastProductTags.all()
           
        for tag in service_tags:
            for serv in ServiceSerializerForPost(Service.objects.filter(SearchNames__Name=tag.Name, Posts__Activated=True),
                                             many=True, context={'request':request}).data:
                if serv not in data['data']:
                    data['data'].append(serv)
            
        
        for serv in ServiceSerializerForPost(Service.objects.filter(SearchNames__Name=profile.LastSearchNotFound, Posts__Activated=True),many=True, 
                                            context={'request':request}).data:
            if serv not in data['data']:
                data['data'].append(serv)

                                            
        for serv in ServiceSerializerForPost(Service.objects.filter(SearchNames__Name=profile.LastSearcheTag, Posts__Activated=True),many=True, 
                                            context={'request':request}).data:
            if serv not in data['data']:
                data['data'].append(serv)

        
        for serv in ServiceSerializerForPost(Service.objects.filter(Type=profile.LastCategory, Posts__Activated=True), many=True, 
                                            context={'request':request}).data:
            if serv not in data['data']:
                data['data'].append(serv)
                
        if len(data['data'])<=15:
            for serv in ServiceSerializerForPost(Service.objects.filter(
                Posts__Activated=True).order_by('-Posts__TotalLikes'), many=True, context={'request':request}).data:
                if serv not in data['data']:
                    data['data'].append(serv)

        return data

        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def posts(request):
    if request.method=='POST':

        data = getPostData(request.data['Username'],request)

        return Response(data)

        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addPostComment(request):
    if request.method=='POST':

        post = Post.objects.get(id=request.data['postId'])

        comment = PostComments.objects.create(Username=request.data['Username'],Comment=request.data['comment'])

        post.Comments.add(comment)
        comment.save()
        post.save()


        if request.data['type']=='myPost':
            profile = Profile.objects.get(User__username=request.data['Username'])
            services = profile.Service.all()
            data={}
            data['data'] = ServiceSerializerForPost(services, many=True, context={'request':request}).data

        else:
            data = getPostData(request.data['Username'],request)

        
        return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def removePostComment(request):
    if request.method=='POST':

        comment = PostComments.objects.get(id=request.data['commentId'])
        comment.delete()

        if request.data['type']=='myPost':
            profile = Profile.objects.get(User__username=request.data['Username'])
            services = profile.Service.all()
            data={}
            data['data'] = ServiceSerializerForPost(services, many=True, context={'request':request}).data

        else:
            data = getPostData(request.data['Username'],request)


        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addPostCommentReply(request):
    if request.method=='POST':

        comment = PostComments.objects.get(id=request.data['commentId'])
        reply = PostCommentsReplies.objects.create(Username=request.data['Username'],Reply=request.data['reply'])

        comment.Replies.add(reply)
        reply.save()
        comment.save()


        if request.data['type']=='myPost':
            profile = Profile.objects.get(User__username=request.data['Username'])
            services = profile.Service.all()
            data={}
            data['data'] = ServiceSerializerForPost(services, many=True, context={'request':request}).data

        else:
            data = getPostData(request.data['Username'],request)


        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def removePostCommentReply(request):
    if request.method=='POST':

        reply = PostCommentsReplies.objects.get(id=request.data['replyId'])
        reply.delete()

        if request.data['type']=='myPost':
            profile = Profile.objects.get(User__username=request.data['Username'])
            services = profile.Service.all()
            data={}
            data['data'] = ServiceSerializerForPost(services, many=True, context={'request':request}).data

        else:
            data = getPostData(request.data['Username'],request)

        return Response(data)


        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addPostLike(request):
    if request.method=='POST':

        profile = Profile.objects.get(User__username=request.data['Username'])
        post = Post.objects.get(id=request.data['postId'])

        if post.LikedBy.filter(id=profile.User.id).exists():
            
            post.LikedBy.remove(profile.User)
            post.TotalLikes = int(post.TotalLikes)-1
        else:
        
            post.LikedBy.add(profile.User)
            post.TotalLikes = int(post.TotalLikes)+1

        service = Service.objects.get(Posts__id=post.id)

        plan = Plans.objects.get(Open=True, PlanName='250')

        if service in plan.PlanServices.all():
            pass
        elif int(post.TotalLikes)>250 :
            post.Activated=False
        post.save()


        if request.data['type']=='myPost':
            services = profile.Service.all()
            data={}
            data['data'] = ServiceSerializerForPost(services, many=True, context={'request':request}).data

        else:
            data = getPostData(request.data['Username'],request)

        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def savePost(request):
    if request.method=='POST':

        profile = Profile.objects.get(User__username=request.data['Username'])

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

        if Profile.objects.filter(User__username=request.data['Username']).exists():
            profile = Profile.objects.get(User__username=request.data['Username'])

        else:
            return Response({'msg':'You are not a Service Provider.'})
            
        services = profile.Service.all()
        data = ServiceSerializerForPost(services, many=True, context={'request':request}).data

        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activatePostTogle(request):
    if request.method=='POST':

        post = Post.objects.get(id=request.data['postId'])

        if post.Activated:
            post.Activated = False

        else:

            plan = Plans.objects.get(Open=True, PlanName='250')

            if Service.objects.get(id=request.data['serviceId']) in plan.PlanServices.all():
                post.Activated = True

            else:

                if post.TotalLikes>250:
                    return Response({'msg':'Call us to reactivate. Your post has over 250 likes'})

                else:

                    post.Activated = True

        post.save()

        if Profile.objects.filter(User__username=request.data['Username']).exists():
            profile = Profile.objects.get(User__username=request.data['Username'])
        else:
            return Response({'msg':'You are not a Service Provider.'})
  
        services = profile.Service.all()
        data = ServiceSerializer(services, many=True, context={'request':request}).data
            
        return Response(data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addNewPost(request):
    if request.method=='POST':

        service = Service.objects.get(id=request.data['selectedServiceId'])

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

        
        profile = Profile.objects.get(User__username=request.data['Username'])
        services = profile.Service.all()
        data = ServiceSerializerForPost(services, many=True, context={'request':request}).data
        return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def savedServices(request):
    if request.method=='POST':

        profile = Profile.objects.get(User__username=request.data['Username'])
        
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

    toComplete = RequestedService.objects.get(id=request.data['id'])
    toComplete.completed=True
    toComplete.save()

    data['msg']='Successfull'
    return Response(data)


@api_view(['POST'])
def addingServiceRequest(request):
    user = User.objects.get(username=request.data['username'])
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