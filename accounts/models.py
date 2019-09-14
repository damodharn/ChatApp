from django.db import models
from django.contrib.auth.models import User


class ChatUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    messages = models.TextField(max_length=5000, blank=True)
    DOB = models.DateField(null=True, blank=True)

