from django.urls import path
from . import views

app_name = 'maps'

urlpatterns = [
    path('', views.main_map_view, name='main_map'),
    path('fetch-details/', views.fetch_school_details_view, name='fetch_school_details'),
    path('list-models/', views.list_gemini_models_view, name='list_gemini_models'),
    path('scraped-posts/', views.scraped_posts_view, name='scraped_posts'),
]