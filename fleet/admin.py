from django.contrib import admin
from .models import Automobile, Driver, TravelLog


@admin.register(Automobile)
class AutomobileAdmin(admin.ModelAdmin):
    list_display = ('make', 'model', 'license_plate', 'current_mileage', 'is_inspection_due', 'is_insurance_due')
    list_filter = ('make',)


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'contact_info')


@admin.register(TravelLog)
class TravelLogAdmin(admin.ModelAdmin):
    list_display = ('log_number', 'start_date', 'automobile', 'driver', 'distance_traveled', 'actual_fuel')
    list_filter = ('start_date', 'automobile', 'driver')
