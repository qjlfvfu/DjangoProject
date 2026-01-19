from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.BlogListView.as_view(), name='blog_list'),
    path('create/', views.BlogCreateView.as_view(), name='blog_create'),
    path('<int:pk>/', views.BlogDetailView.as_view(), name='blog_detail'),
    path('<int:pk>/edit/', views.BlogUpdateView.as_view(), name='blog_edit'),
    path('<int:pk>/delete/', views.BlogDeleteView.as_view(), name='blog_delete'),
]