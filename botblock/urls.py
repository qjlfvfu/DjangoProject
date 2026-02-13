from django.urls import path

from . import views

app_name = "botblock"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),  # Регистрация
    path("login/",views.LoginView.as_view(), name="login"), # Вход
    path("profile/",views.profile_view, name="profile"), # Профиль пользователя
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/my-products/', views.my_products, name='my_products'),
    path('profile/upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
]
