from django.contrib.auth import update_session_auth_hash
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from core.models import Rate
from .forms import AccountRegistrationForm, NewProductForm, UserRegistrationForm, AccountUpdateForm, UserUpdateForm
from django.forms import modelform_factory
from django import forms
from django.http import Http404, HttpResponseRedirect
from django.views.generic import (
	ListView,
	DetailView,
	DeleteView,
	View,
	TemplateView)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Product, Image, Rent, User2
from django.db.models import ProtectedError
from .mixins import check_user


class Home(ListView):
	model = Product
	template_name = 'home.html'
	context_object_name = 'products'
	ordering = ['-date_created']
	paginate_by = 10


class ProductView(DetailView):
	model = Product
	template_name = 'product_view.html'
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		context['is_product_rented_user'] = False if self.object.is_available else \
			Rent.objects.get(product_id=self.object.id).check_user(self.request.user)
		context['is_product_seller'] = self.object.check_owner(self.request.user)
		
		context['rate'], context['rate_count'] = Rate.get_rate(self.object.user_id)
		
		return context


# todo: works of the forms + SignupView recreate + context
# todo: form name change
class SignupView(View):
	def post(self, request, *args, **kwargs):
		form = AccountRegistrationForm(request.POST)
		u_form = UserRegistrationForm(request.POST)
		if form.is_valid() and u_form.is_valid():
			user = form.save()
			u_form = u_form.save(commit=False)  # typeUser
			u_form.user = user
			u_form.save()  # todo image save disable
			messages.success(request, 'Congratulation you\'re signed up.')
			return redirect(reverse('login'))
		else:
			return render(request, 'signup.html', {'form': form, 'u_form': u_form})
	
	def get(self, request, *args, **kwargs):
		form = AccountRegistrationForm()
		u_form = UserRegistrationForm()
		return render(request, 'signup.html', {'form': form, 'u_form': u_form})


# todo: mixin for check user username on url
class ProfileView(UserPassesTestMixin, TemplateView):
	template_name = 'profile_view.html'
	
	def handle_no_permission(self):
		raise Http404
	
	def test_func(self):
		return True if check_user(self.kwargs['username']) else False
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		username: str = kwargs['username']
		
		context['is_owner'] = True if username == self.request.user.username else False
		context['user2'] = User2.objects.get(user_id=User.objects.get(username=username))
		context['products'] = Product.objects.filter(user_id=context['user2'].id)
		context['product_count'] = len(context['products'])
		context['rented_products'] = Rent.get_rent_product(self.request.user.user2.id)
		context['rate_value'], context['rate_count'] = Rate.get_rate(context['user2'].id)
		
		return context


# todo Rentview name change (it is not a view)
class RentView(LoginRequiredMixin, View):
	
	def test_func(self, request, product_id):
		product = Product.objects.get(id=product_id)
		request = self.request
		if not product.is_available:
			messages.warning(request, 'product already rented!')
			return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
		if request.user.id == product.user2.user_id:
			messages.error(request, 'Don\'t you rent your own product')
			return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
		return None
	
	def get(self, request, product_id):
				
		res = self.test_func(request, product_id)
		if not res is None:
			return res

		Rent.rent_process(Product.objects.get(id=product_id), request.user)
		messages.success(request, 'product rented successfully')
		return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


class RentList(LoginRequiredMixin, ListView):
	template_name = 'rent_list.html'
	context_object_name = 'products'
	paginate_by = 20
	
	def get_queryset(self):
		query_set = Product.objects.filter(rent__user2_rented__user_id=self.request.user.id)
		return query_set


class RentReturnView(LoginRequiredMixin, View):
	
	def test_func(self, request, product_id):
		user = request.user
		product = Product.objects.get(id=product_id)
		
		if product.is_available:  # check product rented or not
			messages.success(request, 'Product not rented yet!')
			return redirect('product-view', product_id)
		if not user.id == Rent.objects.get(product_id=product).user2_rented.user_id:  # Check product rented user
			messages.success(request, 'product rented successfully')
			return redirect('home')
	
	def get(self, request, product_id):
		
		res = self.test_func(request, product_id)
		if not res is None:
			return res
		
		Rent.rent_return_process(Product.objects.get(id=product_id))
		messages.success(request, 'product rented successfully')
		return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


class MyProductListView(LoginRequiredMixin, ListView):
	template_name = 'my_product_list.html'
	context_object_name = 'products'
	paginate_by = 20
	
	def get_queryset(self):
		query_set = Product.objects.filter(user2__user_id=self.request.user.id)
		return query_set


class SettingView(LoginRequiredMixin, UserPassesTestMixin, View):
	"""docstring for SettingView"""
	
	def test_func(self):
		return self.kwargs['username'] == self.request.user.username
	
	def post(self, request, username):
		if request.POST['update'] == 'profile':
			a_form = AccountUpdateForm(request.POST, instance=request.user)
			u_form = UserUpdateForm(request.POST, request.FILES, instance=request.user.user2)
			p_form = PasswordChangeForm(request.user)
			if a_form.is_valid() and u_form.is_valid():
				a_form.save()
				u_form.save()
				return redirect('setting-view', request.user.username)
			else:
				messages.error(request, 'Please correct the error below.')
		elif request.POST['update'] == 'password':
			p_form = PasswordChangeForm(request.user, request.POST)
			a_form = AccountUpdateForm(instance=request.user)
			u_form = UserUpdateForm(instance=request.user.user2)
			if p_form.is_valid():
				user = p_form.save()
				update_session_auth_hash(request, user)  # Important!
				return redirect('setting-view', request.user.username)
			else:
				messages.error(request, 'Please correct the error below.')
		else:
			return redirect('setting-view', request.user.username)
		context = {
			'a_form': a_form,
			'u_form': u_form,
			'p_form': p_form
		}
		
		return render(request, 'pref_view.html', context)
	
	def get(self, request, username):
		a_form = AccountUpdateForm(instance=request.user)
		u_form = UserUpdateForm(instance=request.user.user2)
		p_form = PasswordChangeForm(request.user)
		
		context = {
			'a_form': a_form,
			'u_form': u_form,
			'p_form': p_form
		}
		
		return render(request, 'pref_view.html', context)


class EditProduct(LoginRequiredMixin, View):
	
	def test_func(self, request, product_id):
		product = Product.objects.get(id=self.kwargs['product_id'])
		
		if self.request.user == User2.objects.get(id=product.user2.user_id):
			return render(self.request, '403.html', status=403)
		
		if not product.is_available:
			messages.error(request, 'Please clear the rents before edit')
			return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
		return None
	
	def post(self, request, product_id):
		
		res = self.test_func(request, product_id)
		if not res is None:
			return res
		
		product = Product.objects.get(id=product_id)
		img_form = modelform_factory(Image, fields=['image'],
		                             widgets={'image': forms.ClearableFileInput(attrs={'multiple': True})})
		form = NewProductForm(request.POST, instance=product)
		img_form = img_form(request.POST, request.FILES)
		if form.is_valid() and img_form.is_valid():
			edited_product = form.save()
			files = request.FILES.getlist('image', settings.DEFAULT_PRODUCT_IMAGE)
			
			for old_image in Image.objects.filter(product_id=edited_product.id):  # delete old image in database
				old_image.delete()
			
			for index, f in enumerate(files):  # create new image in database
				Image(image=f, product_id=edited_product.id, is_primary=True if index == 0 else False).save()
			
			return redirect('edit-product', product_id)
		else:
			messages.error(request, 'following encountered!')
			return render(request, 'edit_product.html', {'form': form, 'image_form': img_form})
	
	def get(self, request, product_id):
		
		res = self.test_func(request, product_id)
		if not res is None:
			return res
		
		product = Product.objects.get(id=product_id)
		img_form = modelform_factory(Image, fields=['image'],
		                             widgets={'image': forms.ClearableFileInput(attrs={'multiple': True})})
		form = NewProductForm(instance=product)
		return render(request, 'edit_product.html', {'form': form, 'image_form': img_form})


class RemoveProduct(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
	model = Product
	template_name = 'remove_product.html'
	success_url = '/'
	
	def test_func(self):
		product = self.get_object()
		if self.request.user.id == product.user2.user2_id and product.is_available:
			return True
		messages.error(self.request, 'Clear the rents before delete the product.')
		return False
	
	def post(self, request, *args, **kwargs):
		try:
			return self.delete(request, *args, **kwargs)
		except ProtectedError:
			return redirect('/')


class ProductListView(ListView):
	model = Product
	template_name = 'home.html'
	context_object_name = 'products'
	ordering = ['-date_posted']
	paginate_by = 5


class NewProduct(LoginRequiredMixin, View):
	"""docstring for NewProduct"""
	
	def post(self, request):
		img_form = modelform_factory(Image, fields=['image'],
		                             widgets={'image': forms.ClearableFileInput(attrs={'multiple': True})})
		form = NewProductForm(request.POST)
		img_form = img_form(request.POST, request.FILES)
		if form.is_valid() and img_form.is_valid():
			files = request.FILES.getlist('image', 'default.jpg')
			prod: Product = form.save(commit=False)
			user = User2.objects.get(user=request.user)
			prod.user2 = user
			prod.save()
			for index, f in enumerate(files):
				ins = Image(image=f, product=prod, is_primary=True if index == 0 else False)
				ins.save()
			redirect('/product/new')
		else:
			raise Http404
		return render(request, 'new_product.html', {'form': form, 'image_form': img_form})
	
	def get(self, request):
		img_form = modelform_factory(Image, fields=['image'],
		                             widgets={'image': forms.ClearableFileInput(attrs={'multiple': True})})
		form = NewProductForm()
		return render(request, 'new_product.html', {'form': form, 'image_form': img_form})


class DeleteAccount(LoginRequiredMixin, UserPassesTestMixin, View):
	
	def handle_no_permission(self):
		return render(self.request, '403.html', status=403)
	
	def test_func(self):
		return self.request.user.username == self.request.kwargs['username']
	
	def post(self, request):
		user2_id = request.user.user2.id
		selling_product_ids = [p.id for p in Product.objects.filter(user2_id=user2_id)]
		all_rented_product_ids = [p.product_id for p in Rent.objects.all()]
		
		def is_someone_rented_his_product():
			for t in all_rented_product_ids:
				for r in selling_product_ids:
					if r == t:
						return True
			return False
		
		if Rent.objects.filter(user2_rented_id=user2_id).exists() or is_someone_rented_his_product():
			messages.error(request, 'Please clear the rents')
			return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
		user = request.user
		if not user.check_password(request.POST['password']):
			messages.error(request, 'password did\'nt match')
			return render(request, 'delete_account.html')
		try:
			user.delete()
			messages.success(request, 'Your Account was deleted!')
		except Exception as e:
			messages.error(request, e.__str__())
		return redirect('login')
	
	def get(self, request):
		user2_id = request.user.user2.id
		selling_product_ids = [p.id for p in Product.objects.filter(user2_id=user2_id)]
		all_rented_product_ids = [p.product_id for p in Rent.objects.all()]
		
		def is_someone_rented_his_product():
			for t in all_rented_product_ids:
				for r in selling_product_ids:
					if r == t:
						return True
			return False
		
		if Rent.objects.filter(user2_rented_id=user2_id).exists() or is_someone_rented_his_product():
			messages.error(request, 'Please clear the rents')
			return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
		return render(request, 'delete_account.html')


class AddRate(LoginRequiredMixin, View): # rate/<int:user_id>/
	
	def test_func(self, request, user_id):
		if request.user.user2.id == user_id:
			return render(request, '403.html', status=403)
		
		if not User.objects.all().filter(pk=user_id).exists():
			return render(request, '403.html', status=403)

		lessor = User2.objects.get(id=user_id) # lessor
				
		if not Rent.is_any_rented(lessor, request.user.user2):
			return render(request, '403.html', status=403)
		
		if not 0 < int(request.POST['value']) < 10:
			return render(request, '403.html', status=403)

		return None
	
	def post(self, request, user_id):
		res = self.test_func(request, user_id)
		if not res is None:
			return res

		user = request.user # lessee
		lessor = User2.objects.get(id=user_id) # lessor
		
		lessor_lessee_rents = Rate.objects.all().filter(user_rated_id=user.user2.id, user_rated_to_id=user_id)		

		if lessor_lessee_rents.exists():
			if lessor_lessee_rents.count() > 1:
				for rate in lessor_lessee_rents:
					rate.delete()
				new_rate = True
			else:
				new_rate = False
		else:
			new_rate = True
		
		if new_rate:
			Rate(rate_value=int(request.POST['value']), user_rated_id=user.user2.id,
			     user_rated_to_id=user_id).save()
		else:
			rate = Rate.objects.get(user_rated_id=user.user2.id, user_rated_to_id=user_id)
			rate.rate_value = request.POST['value']
			rate.save()
		
		return redirect('profile-view', username=lessor.user.username)
	
	def get(self, request):
		return render(request, 'rate.html')


class DeleteRate(LoginRequiredMixin, View):
	
	def test_func(self, request, user_id):
		
		if request.user.user2.id == user_id:
			return render(request, '403.html', status=403)
		
		if not User2.objects.all().filter(pk=user_id).exists():
			return render(request, '403.html', status=403)
		return None
	
	def post(self, request, user_id):
		
		res = self.test_func(request, user_id)
		if not res is None:
			return res

		user: User = request.user
		u2 = User2.objects.get(id=user_id)
		
		if Rate.objects.all().filter(user2_rated_id=user.user2.id, user2_rated_to_id=user_id).exists():
			for rate in Rate.objects.all().filter(user2_rated_id=user.user2.id, user2_rated_to_id=user_id):
				rate.delete()
		else:
			raise Http404
		return redirect('profile-view', username=u2.user.username)
	
	def get(self, request, user_id):
		return redirect('add_rate', user_id=user_id)
