from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Q
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Automobile, Driver, TravelLog
from .forms import AutomobileForm, DriverForm, TravelLogForm, UserRegistrationForm, UserEditForm, ReportFilterForm


def is_admin(user):
    return user.groups.filter(name='Administrator').exists() or user.is_superuser


def is_mechanic(user):
    return user.groups.filter(name='Mechanic').exists() or user.is_superuser


def is_dispatcher(user):
    return user.groups.filter(name='Dispatcher').exists() or user.is_superuser


def is_accountant(user):
    return user.groups.filter(name='Accountant').exists() or user.is_superuser


@login_required
def get_car_mileage(request, car_id):
    car = get_object_or_404(Automobile, pk=car_id)
    return JsonResponse({'current_mileage': car.current_mileage})


@login_required
def dashboard(request):
    context = {
        'cars_count': Automobile.objects.count(),
        'drivers_count': Driver.objects.count(),
        'logs_count': TravelLog.objects.count(),
    }

    if is_admin(request.user):
        context['employees_count'] = User.objects.exclude(is_superuser=True).count()

    if is_mechanic(request.user) or is_dispatcher(request.user):
        cars = Automobile.objects.all()
        warnings = []
        for car in cars:
            if car.is_inspection_due():
                warnings.append(f"Транспорт {car.license_plate}: истекает Техосмотр ({car.inspection_due_date})")
            if car.is_insurance_due():
                warnings.append(f"Транспорт {car.license_plate}: истекает Страховка ({car.insurance_due_date})")
        context['warnings'] = warnings

    return render(request, 'fleet/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Новый сотрудник успешно добавлен!")
            return redirect('employee_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'fleet/register_user.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def employee_list(request):
    employees = User.objects.all().prefetch_related('groups', 'profile').order_by('id')
    return render(request, 'fleet/employee_list.html', {'employees': employees})


@login_required
@user_passes_test(is_admin)
def employee_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Данные сотрудника обновлены.")
            return redirect('employee_list')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'fleet/register_user.html', {'form': form, 'title': 'Редактирование сотрудника'})


@login_required
@user_passes_test(is_admin)
def employee_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, "Сотрудник удален.")
        return redirect('employee_list')
    return render(request, 'fleet/employee_confirm_delete.html', {'employee': user})


@login_required
@user_passes_test(is_admin)
def driver_list(request):
    drivers = Driver.objects.all()
    return render(request, 'fleet/driver_list.html', {'drivers': drivers})


@login_required
@user_passes_test(is_admin)
def driver_create(request):
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('driver_list')
    else:
        form = DriverForm()
    return render(request, 'fleet/driver_form.html', {'form': form, 'title': 'Добавить водителя'})


@login_required
@user_passes_test(is_admin)
def driver_edit(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            return redirect('driver_list')
    else:
        form = DriverForm(instance=driver)
    return render(request, 'fleet/driver_form.html', {'form': form, 'title': 'Редактировать водителя'})


@login_required
@user_passes_test(is_admin)
def driver_delete(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        driver.delete()
        messages.success(request, "Водитель удален.")
        return redirect('driver_list')
    return render(request, 'fleet/driver_confirm_delete.html', {'driver': driver})


@login_required
@user_passes_test(is_mechanic)
def car_list(request):
    query = request.GET.get('q')
    if query:
        cars = Automobile.objects.filter(license_plate__icontains=query)
    else:
        cars = Automobile.objects.all()
    return render(request, 'fleet/car_list.html', {'cars': cars, 'query': query})


@login_required
@user_passes_test(is_mechanic)
def car_create(request):
    if request.method == 'POST':
        form = AutomobileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('car_list')
    else:
        form = AutomobileForm()
    return render(request, 'fleet/car_form.html', {'form': form, 'title': 'Добавить автомобиль'})


@login_required
@user_passes_test(is_mechanic)
def car_edit(request, pk):
    car = get_object_or_404(Automobile, pk=pk)
    if request.method == 'POST':
        form = AutomobileForm(request.POST, instance=car)
        if form.is_valid():
            form.save()
            return redirect('car_list')
    else:
        form = AutomobileForm(instance=car)
    return render(request, 'fleet/car_form.html', {'form': form, 'title': 'Редактировать автомобиль'})


@login_required
@user_passes_test(is_mechanic)
def car_delete(request, pk):
    car = get_object_or_404(Automobile, pk=pk)
    if request.method == 'POST':
        car.delete()
        messages.success(request, "Автомобиль удален.")
        return redirect('car_list')
    return render(request, 'fleet/car_confirm_delete.html', {'car': car})


@login_required
@user_passes_test(is_dispatcher)
def log_list(request):
    logs = TravelLog.objects.all().order_by('-start_date', '-id')
    return render(request, 'fleet/log_list.html', {'logs': logs})


@login_required
@user_passes_test(is_dispatcher)
def log_create(request):
    if request.method == 'POST':
        form = TravelLogForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('log_list')
    else:
        form = TravelLogForm()
    return render(request, 'fleet/log_form.html', {'form': form, 'title': 'Создать путевой лист'})


@login_required
@user_passes_test(is_dispatcher)
def log_detail(request, pk):
    log = get_object_or_404(TravelLog, pk=pk)
    return render(request, 'fleet/log_detail.html', {'log': log})


@login_required
@user_passes_test(is_accountant)
def reports_selection(request):
    form = ReportFilterForm(request.GET)
    return render(request, 'fleet/report_selection.html', {'form': form})


@login_required
@user_passes_test(is_accountant)
def reports_result(request):
    logs = TravelLog.objects.all()

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    automobile_id = request.GET.get('automobile')
    driver_id = request.GET.get('driver')

    if date_from:
        logs = logs.filter(start_date__gte=date_from)
    if date_to:
        logs = logs.filter(start_date__lte=date_to)
    if automobile_id:
        logs = logs.filter(automobile_id=automobile_id)
    if driver_id:
        logs = logs.filter(driver_id=driver_id)

    total_distance = sum(log.distance_traveled for log in logs)
    total_fuel_norm = sum(log.normative_fuel for log in logs)
    total_fuel_actual = sum(log.actual_fuel for log in logs)

    context = {
        'logs': logs,
        'date_from': date_from,
        'date_to': date_to,
        'total_distance': round(total_distance, 2),
        'total_fuel_norm': round(total_fuel_norm, 2),
        'total_fuel_actual': round(total_fuel_actual, 2),
        'economy': round(total_fuel_norm - total_fuel_actual, 2)
    }
    return render(request, 'fleet/report_result.html', context)
