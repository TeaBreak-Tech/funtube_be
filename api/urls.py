from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('session', views.new_session),
    path('logout', views.logout),
    path('video/', views.add_video),
    path('video/list', views.get_video_list),
    path('video/load', views.load_video_list),
    path('event/', views.new_event),
    #path('videos/', views.get_tagged_video_list),
    path('video_by_tag/<str:cat_id>/', views.get_video_by_tag),
    path('video_tag/', views.add_video_tag),
    path('suggestion',views.getSuggestion),
    path('cat',views.getCategories),
    path('videos',views.getHistory),
    path('ads',views.getViewedAds),
    path('ad_plan',views.getAdPlan),
    path('data/visitorlist',views.listAllVisitors),
    path('data/visitor/<pid>',views.showVisitorInfo),
    path('',views.getCategories),
]