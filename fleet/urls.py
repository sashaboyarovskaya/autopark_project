from django.urls import path, include
from . import views

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),

    path('', views.dashboard, name='dashboard'),

    path('admin-panel/employees/', views.employee_list, name='employee_list'),
    path('admin-panel/employees/add/', views.register_user, name='register_user'),
    path('admin-panel/employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('admin-panel/employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),

    path('cars/', views.car_list, name='car_list'),
    path('cars/add/', views.car_create, name='car_create'),
    path('cars/<int:pk>/edit/', views.car_edit, name='car_edit'),
    path('cars/<int:pk>/delete/', views.car_delete, name='car_delete'),
    path('cars/api/get_mileage/<int:car_id>/', views.get_car_mileage, name='get_car_mileage'),

    path('drivers/', views.driver_list, name='driver_list'),
    path('drivers/add/', views.driver_create, name='driver_create'),
    path('drivers/<int:pk>/edit/', views.driver_edit, name='driver_edit'),
    path('drivers/<int:pk>/delete/', views.driver_delete, name='driver_delete'),

    path('logs/', views.log_list, name='log_list'),
    path('logs/add/', views.log_create, name='log_create'),
    path('logs/<int:pk>/', views.log_detail, name='log_detail'),

    path('reports/', views.reports_selection, name='reports_selection'),
    path('reports/view/', views.reports_result, name='reports_result'),
]
