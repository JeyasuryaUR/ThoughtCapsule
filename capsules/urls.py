from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_capsule, name='create_capsule'),
    path('<int:pk>/', views.capsule_detail, name='capsule_detail'),
    path('<int:pk>/edit/', views.edit_capsule, name='edit_capsule'),
    path('<int:pk>/delete/', views.delete_capsule, name='delete_capsule'),
    path('tag/<int:pk>/', views.tag_detail, name='tag_detail'),
    path('search/', views.search, name='search'),
    path('generate-tags/', views.generate_tags_view, name='generate-tags'),
    path('summarize/', views.summarize_view, name='summarize'),
    path('my_capsules/', views.my_capsules, name='my_capsules'),
    path('categories/<int:cid>', views.categories_view, name='category'),
    path('analytics/', views.analytics_view, name='analytics'),
]