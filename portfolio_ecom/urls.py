from django.contrib import admin
from django.urls import path, include, re_path
from core import views
from django.contrib.auth.views import LoginView, LogoutView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
urlpatterns = [

    path('product/new/', views.NewProduct.as_view(), name='new-product'),
    path('product/<int:pk>/', views.ProductView.as_view(), name='product-view'),
    path('product/<int:product_id>/rent/', views.RentView.as_view(), name='rent-view'),
    path('product/<int:product_id>/return/', views.RentReturnView.as_view(), name='rent-return-view'),
    path('product/<int:product_id>/edit/', views.EditProduct.as_view(), name='edit-product'),
    path('product/<int:pk>/remove/', views.RemoveProduct.as_view(), name='remove-product'),

    path('rate/<int:user_id>/', views.AddRate.as_view(), name='add_rate'),
    path('rate/<int:user_id>/delete/', views.DeleteRate.as_view(), name='delete_rate'),

    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout', LogoutView.as_view(template_name='home.html'), name='logout'),
    path('signup/', views.SignupView.as_view(), name='signup'),

    path('reset-password/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name= 'registration/password_reset_email.html',
        subject_template_name = 'registration/password_reset_subject.txt'
    ), name= 'password_reset'),
    path('reset-password-done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset-password-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    path('<str:username>/', views.ProfileView.as_view(), name='profile-view'),
    path('<str:username>/rents/', views.RentList.as_view(), name='rent-list'),
    path('<str:username>/my-products/', views.MyProductListView.as_view(), name='my-products'),
    path('<str:username>/preferences/', views.SettingView.as_view(), name='setting-view'),
    path('<str:username>/delete/', views.DeleteAccount.as_view(), name='account-delete-view'),

    path('admin/', admin.site.urls),


    path('', views.ProductListView.as_view(), name='home')
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
