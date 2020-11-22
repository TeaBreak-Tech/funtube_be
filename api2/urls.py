from django.urls import path

from . import views

urlpatterns = [
    path('good', views.good, name='good'),
    path('user', views.user, name='user'),
    path('cart', views.cart, name='cart'),
    path('label', views.good_label, name='label'),
    path('category',views.category, name='category'),
    path('generate-suggestions',views.generateSuggestions),
    path('suggestion', views.suggestion, name='suggestion')
]