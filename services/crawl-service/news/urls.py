from django.urls import path

from news.views.news import CompanyNewsView

urlpatterns = [
  path('news', CompanyNewsView.as_view(), name='company-news'),
]