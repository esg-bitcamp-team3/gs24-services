from django.urls import path

from finance.views.financial import SingleCompanyFinancialAPIView
from finance.views.company import CompanyView
from finance.views.financial_data import FinancialDataView
from finance.views.stock import StockView, StockHistoryView

urlpatterns = [
  path('stock', StockView.as_view(), name='stock'),
  path('stock-history', StockHistoryView.as_view(), name='stock-history'),
  path('financial-data', FinancialDataView.as_view(), name='financial-data'),
  path('single-financial', SingleCompanyFinancialAPIView.as_view(), name='single-financial'),
  path('company',CompanyView.as_view(), name='company'),
]