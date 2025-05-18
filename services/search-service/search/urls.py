from django.urls import path

from search.views.search_news import SearchNewsView, KeyWordNewsView
from search.views.sentiment import TextSentimentAnalysisView, KeywordSentimentAnalysisView
from search.views.datalab import DatalabKeywordView

urlpatterns = [
  path('news', SearchNewsView.as_view(), name='news'),
  path('keyword-news', KeyWordNewsView.as_view(), name='keyword-news'),
  path('sentiment', TextSentimentAnalysisView.as_view(), name='sentiment'),
  path('keyword-sentiment', KeywordSentimentAnalysisView.as_view(), name='keyword-sentiment'),
  path('keyword-data', DatalabKeywordView.as_view(), name='keyword-data'),
]