from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import *

app_name = 'main'

urlpatterns = [
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('login/', customLogin, name='customLogin'),
    path('forgotpass/', forgotpass, name='forgotpass'),
    path('mainPageData/', mainPageData,name='main_page_data'),
    path('getCategories/', getCategories,name='getCategories'),
    path('messageBox/', messageBox, name='messageBox'),
    path('messages/', messages, name='messages'),
    path('addMessages/', addMessages, name='addMessages'),
    path('signupAsProvider/', signupAsProvider,name='signupAsProvider'),
    path('logout/', logingout, name='logout'),
    path('addFeedback/', addFeedback, name='addFeedback'),
    path('account/', account, name='account'),
    path('setFirstname/',setFirstname, name='setFirstname'),
    path('setLastname/',setLastname, name='setLastname'),
    path('setEmail/',setEmail, name='setEmail'),
    path('setPassword/',setPassword, name='setPassword'),
    path('setMyAddr/',setMyAddr, name='setMyAddr'),
    path('setLoc/',setLoc, name='setLoc'),
    path('setMyNo/',setMyNo, name='setMyNo'),
    path('setShopName/',setShopName, name='setShopName'),
    path('ShopCatagories/',getCategories, name='getCategories'),
    path('updateShopCatagory/',updateShopCatagory, name='updateShopCatagory'),
    path('updateMainImage/',updateMainImage, name='updateMainImage'),
    path('updateImage/',updateImage, name='updateImage'),
    path('addNewImage/',addNewImage,name='addNewImage'),
    path('setOpenTime/',setOpenTime,name='setOpenTime'),
    path('setCloseTime/',setCloseTime,name='setCloseTime'),
    path('setRentalStatus/',setRentalStatus,name='setRentalStatus'),
    path('setGetNotification/',setGetNotification,name='setGetNotification'),
    path('setNoOfItems/',setNoOfItems,name='setNoOfItems'),
    path('setPriceType/',setPriceType,name='setPriceType'),
    path('updateServiceAddr/',updateServiceAddr,name='updateServiceAddr'),
    path('deleteSearchName/',deleteSearchName,name='deleteSearchName'),
    path('deleteImage/',deleteImage,name='deleteImage'),
    path('addSearchName/',addSearchName,name='addSearchName'),
    path('addNewService/',addNewService,name='addNewService'),
    path('search/',search,name='search'),
    path('productData/',productData,name='productData'),
    path('addNewSmsBox/',addNewSmsBox,name='addNewSmsBox'),
    path('giveRating/',giveRating,name='giveRating'),
    path('addServiceFeed/',addServiceFeed,name='addServiceFeed'),
    path('updateDesc/',updateDesc,name='updateDesc'),
    path('removeItem/',removeItem,name='removeItem'),
    path('FAQData/',FAQData,name='FAQData'),
    path('posts/',posts,name='posts'),
    path('morePosts/',morePosts,name='morePosts'),
    path('addPostComment/',addPostComment,name='addPostComment'),
    path('removePostComment/',removePostComment,name='removePostComment'),
    path('addPostCommentReply/',addPostCommentReply,name='addPostCommentReply'),
    path('removePostCommentReply/',removePostCommentReply,name='removePostCommentReply'),
    path('addPostLike/',addPostLike,name='addPostLike'),
    path('savePost/',savePost,name='savePost'),
    path('myPosts/',myPosts,name='myPosts'),
    path('activatePostTogle/',activatePostTogle,name='activatePostTogle'),
    path('addNewPost/',addNewPost,name='addNewPost'),
    path('savedServices/',savedServices,name='savedServices'),
    path('requestedServices/',requestedServices,name='requestedServices'),
    path('completedRequestService/',completedRequestService,name='completedRequestService'),
    path('addingServiceRequest/',addingServiceRequest,name='addingServiceRequest'),
    path('confirm-email/<int:id>/',sentMail,name='sentMail'),
    path('reset-pass/<int:id>/',resetPass,name='resetPass'),
    path('configEmail/',configEmail,name='configEmail'),
    path('rentnow/',rentNow,name='rentNow'),
    path('rentnowconfirmed/',rentNowConfirmed,name='rentNowConfirmed'),
    path('category/<int:id>',getCategoryData,name='getCategoryData'),
    path('sendVerifyEmail/',sendVerifyEmail,name='sendVerifyEmail'),
    path('sendGetProductEmail/',sendGetProductEmail,name='sendGetProductEmail'),
]


















