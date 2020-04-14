# from django.views.generic.base import ContextMixin
# from django.views.generic.detail import BaseDetailView
# from core.models import Rent, Rate
from django.contrib.auth.models import User



def check_user(username):
	for u in User.objects.all():
		if u.username == username:
			return username
	return False