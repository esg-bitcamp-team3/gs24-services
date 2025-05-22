from django.urls import path

from news.views.news import CompanyNewsView
from news.views.final import FinalCompanyNewsView
from news.views.predict import PredictESTRatingsView

urlpatterns = [
  path('news', CompanyNewsView.as_view(), name='company-news'),
  path('final', FinalCompanyNewsView.as_view(), name='company-news'),
  path('predict', PredictESTRatingsView.as_view(), name='company-news'),
]