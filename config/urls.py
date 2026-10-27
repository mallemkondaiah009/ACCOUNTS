"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from masters.views import (
    DashboardAPIView,
    FirmMasterPageView,
    GroupMasterPageView,
    LedgerMasterPageView,
    CashReceiptPageView,
    CashPaymentPageView,
    BankPaymentPageView,
    BankReceiptPageView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', DashboardAPIView.as_view(), name='dashboard'),
    path('firms/', FirmMasterPageView.as_view(), name='firm-master-page'),
    path('groups/', GroupMasterPageView.as_view(), name='group-master-page'),
    path('ledgers/', LedgerMasterPageView.as_view(), name='ledger-master-page'),
    path('cash-receipt/', CashReceiptPageView.as_view(), name='cash-receipt-page'),
    path('cash-payment/', CashPaymentPageView.as_view(), name='cash-payment-page'),
    path('bank-payment/', BankPaymentPageView.as_view(), name='bank-payment-page'),
    path('bank-receipt/', BankReceiptPageView.as_view(), name='bank-receipt-page'),
    path('api/', include('masters.urls')),
]



