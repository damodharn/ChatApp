from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', consumers.ChatConsumer),
    # path('ws/rooms/<uri:str>/', consumers.ChatConsumer),
]
