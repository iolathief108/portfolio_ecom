from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.signals import pre_delete, pre_save, post_delete
from PIL import Image as PilImage
import os
from uuid import uuid4

from django.utils import timezone
from django.utils.deconstruct import deconstructible


@deconstructible
class UserProfileImageName(object):
	
	def __init__(self, path):
		self.sub_path = path
	
	def __call__(self, instance, filename):
		ext = filename.split('.')[-1]
		# get filename
		if instance.profile_pic:
			filename = '{}-{}.{}'.format(instance.id, instance.account.username, ext)
		else:
			# set filename as random string
			filename = '{}.{}'.format(uuid4().hex, ext)
		# return the whole path to the file
		return os.path.join(self.sub_path, filename)


class User2(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	description = models.TextField()
	profile_pic = models.ImageField(default=settings.DEFAULT_PROFILE_IMAGE,
	                                upload_to=UserProfileImageName('user_profile'))
	
	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		
		super().save(force_insert, force_update, using, update_fields)
		
		if self.profile_pic.url.endswith(settings.DEFAULT_PROFILE_IMAGE):
			return
		
		img = PilImage.open(self.profile_pic.path)
		if not img.width == img.height:
			bis_y = img.width > img.height
			b = img.height if bis_y else img.width
			a = img.width if bis_y else img.height
			c = b
			coordinate = ((a - c) / 2, 0, (a + c) / 2, b) if bis_y else (0, (a - c) / 2, b, (a + c) / 2)
			img = img.crop(coordinate)
		if img.height > 450 or img.width > 450:
			img.thumbnail((450, 450))
		
		img.save(self.profile_pic.path)
	
	def __str__(self):
		return f'@{self.user.username}'


class Category(models.Model):
	parent = models.SmallIntegerField(null=True)
	name = models.CharField(max_length=50)
	is_selectable = models.BooleanField(default=True)
	
	def __str__(self):
		return f'{self.name}'


class Country(models.Model):
	name = models.CharField(max_length=35)
	
	def __str__(self):
		return f'{self.name}'


class Product(models.Model):
	user = models.ForeignKey(User2, on_delete=models.CASCADE)
	name = models.CharField(max_length=150)
	brand = models.CharField(max_length=150)
	daily_cost = models.IntegerField()
	deposit_amount = models.IntegerField()
	description = models.CharField(max_length=500)
	is_available = models.BooleanField(default=True)
	category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)
	country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL)
	date_created = models.DateField(auto_now_add=True)
	
	def __str__(self):
		return f'product - {self.name}'
	
	def check_owner(self, user) -> bool:
		if isinstance(user, User):
			return self.user.user_id == user.id
		elif isinstance(user, User2):
			return self.user_id == user.user_id
		return False

@deconstructible
class UploadToPathAndRename(object):
	
	def __init__(self, path):
		self.sub_path = path
	
	def __call__(self, instance, filename):
		ext = filename.split('.')[-1]
		# get filename
		if instance.image:
			
			filename = '{}-{}-{}.{}'.format(instance.image.instance.product.user_id, instance.image.instance.product.id,
			                                instance.image.instance.product.name, ext)
		else:
			# set filename as random string
			filename = '{}.{}'.format(uuid4().hex, ext)
		# return the whole path to the file
		return os.path.join(self.sub_path, filename)


class Image(models.Model):
	# image = models.ImageField(default='default.jpg', upload_to='product_images')
	image = models.ImageField(default='default.jpg', upload_to=UploadToPathAndRename('product_images'))
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	is_primary = models.BooleanField(default=False)
	
	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		super().save(force_insert, force_update, using, update_fields)
		img = PilImage.open(self.image.path)
		if not img.width == img.height:
			bis_y = img.width > img.height
			b = img.height if bis_y else img.width
			a = img.width if bis_y else img.height
			c = b
			coordinate = ((a - c) / 2, 0, (a + c) / 2, b) if bis_y else (0, (a - c) / 2, b, (a + c) / 2)
			img = img.crop(coordinate)
		if img.height > 450 or img.width > 450:
			img.thumbnail((450, 450))
		
		img.save(self.image.path)


class Rate(models.Model):
	user_rated = models.ForeignKey(User2, on_delete=models.CASCADE, related_name='user_rated_id')
	user_rated_to = models.ForeignKey(User2, on_delete=models.CASCADE, related_name='user_rated_to_id')
	rate_value = models.SmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
	
	@classmethod
	def get_rate(cls, seller_id):
		if cls.objects.filter(user_rated_to_id=seller_id).exists():
			rates = [p.rate_value for p in cls.objects.filter(user_rated_to_id=seller_id)]
			total = 0
			for r in rates:
				total += r
			
			mid_val = total / len(rates)
			
			return round(mid_val, 2), len(rates)
		return 0, 0


class Rent(models.Model):
	user_rented = models.ForeignKey(User2, on_delete=models.CASCADE)
	product = models.OneToOneField(Product, on_delete=models.PROTECT)
	rent_date = models.DateField(auto_now_add=True)
	
	def check_user(self, user: User):
		return self.user_rented.id == user.id
	

	@classmethod
	def is_any_rented(cls, lessor: User2, lessee: User2):
		lessee_rents = lessee.rent_set.all()
		lessor_rent_products = lessor.product_set.all()
		
		for lessor_rent in lessee_rents:
			for lessor_rent_product in lessor_rent_products:
				if lessor_rent_product.id == lessor_rent.product_id:
					return True
		return False


	@classmethod
	def get_rent_product(cls, user2_id):
		rented_products = []
		rents = cls.objects.filter(user_rented_id=user2_id)
		for rented_product in rents:
			rented_products.append(rented_product.product)
		return rented_products
	
	@classmethod
	def rent_process(cls, product, user_rented):
		"""
		:type product: Product
		:type user_rented: Account
		"""
		rent_obj = cls(user_rented=User.objects.get(account_id=user_rented.id), product=product,
		               rent_date=timezone.now())
		rent_obj.save()
		product.is_available = False
		product.save()
	
	@classmethod
	def rent_return_process(cls, product):
		"""
		:type product: Product
		"""
		rent_obj = cls.objects.get(product_id=product.id)
		rent_obj.delete()
		product.is_available = True
		product.save()


def profile_image_update(sender, **kwargs):
	user: User2 = kwargs['instance']
	if user.id:
		# default_url = '/media/default.jpg'
		default_url = settings.DEFAULT_PROFILE_IMAGE
		old_path = User2.objects.get(id=user.id).profile_pic.path
		old_url = User2.objects.get(id=user.id).profile_pic.url
		new_url = user.profile_pic.url
		if old_url == default_url or old_url == new_url:
			return
		try:
			os.remove(old_path)
		except FileNotFoundError:
			print(f'file path {old_path} not found!')
	return


pre_delete.connect(profile_image_update, sender=User2)
pre_save.connect(profile_image_update, sender=User2)


def product_image_delete(sender, **kwargs):
	img: Image = kwargs['instance']
	try:
		os.remove(img.image.path)
	except FileNotFoundError:
		print(f'file path {img.image.path} not found')


post_delete.connect(product_image_delete, sender=Image)
