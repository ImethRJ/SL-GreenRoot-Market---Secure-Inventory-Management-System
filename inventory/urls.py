from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth Views
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Dashboard & Pages
    path('', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('pos/', views.pos_view, name='pos_view'),

    # APIs
    path('api/products/search/', views.product_search_api, name='product_search_api'),
    path('api/pos/lookup/', views.pos_product_lookup, name='pos_product_lookup'),
    path('api/pos/checkout/', views.pos_checkout, name='pos_checkout'),
]
