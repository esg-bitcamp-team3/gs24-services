from django.urls import path

from market.views.carbon_price import CarbonPriceView
from market.views.exchange_rate import ExchangeRateView

urlpatterns = [
  path('carbon-price', CarbonPriceView.as_view(), name='carbon_price'),
  path('exchange-rate', ExchangeRateView.as_view(), name='exchange_rate'),
]