
from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
     path('platforms/', views.platform_list, name='platform_list'),
    path('platforms/add/', views.platform_create, name='platform_add'),
    path('platforms/edit/<int:pk>/', views.platform_edit, name='platform_edit'),
    path('platforms/delete/<int:pk>/', views.platform_delete, name='platform_delete'),
  
    path('tracking/', views.param_index, name='param_index'),
    path('tracking/<int:pk>/json/', views.param_detail_json, name='param_detail_json'),
    path('tracking/<int:pk>/delete/', views.param_delete, name='param_delete'),
    # Admin-only screens for Offer Links (hidden for non-staff in navbar)
    path("offers/", views.offer_index, name="offer_index"),
    path("offers/upload/", views.upload_offer_links, name="upload_offer_links"),
    
    path("offers/link/add/", views.offer_link_add, name="offer_link_add"),
    path("offers/link/<int:pk>/edit/", views.offer_link_edit, name="offer_link_edit"),
    path("offers/link/<int:pk>/delete/", views.offer_link_delete, name="offer_link_delete"),
    
    path("offer/network/add/",views.offer_network_add, name="offer_network_add"),
    path("offers/network/<int:pk>/edit/", views.offer_network_edit, name="offer_network_edit"),
    path("offers/network/<int:pk>/delete/", views.offer_network_delete, name="offer_network_delete"),
    
    path("offer/add",views.offer_add,name="offer_add"),
    path("offers/<int:pk>/edit/", views.offer_edit, name="offer_edit"),
    path("offers/<int:pk>/delete/", views.offer_delete, name="offer_delete"),
    
    path("personalized-tags/", views.personalized_tag_list, name="personalized_tag_list"),
    path("personalized-tags/add/", views.personalized_tag_create, name="personalized_tag_add"),
    path("personalized-tags/<int:pk>/edit/", views.personalized_tag_edit, name="personalized_tag_edit"),
    path("personalized-tags/<int:pk>/delete/", views.personalized_tag_delete, name="personalized_tag_delete"),

]
