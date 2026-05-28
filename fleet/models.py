from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


def get_next_log_number():
    last_log = TravelLog.objects.order_by('id').last()
    if not last_log:
        return "1"
    try:
        return str(int(last_log.log_number) + 1)
    except ValueError:
        return str(last_log.id + 1)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    middle_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Отчество")
    phone_number = models.CharField(max_length=20, verbose_name="Номер телефона")

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)


class Driver(models.Model):
    last_name = models.CharField(max_length=50, verbose_name="Фамилия", default="")
    first_name = models.CharField(max_length=50, verbose_name="Имя", default="")
    middle_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Отчество")
    contact_info = models.CharField(max_length=200, verbose_name="Контактные данные")

    def __str__(self):
        if self.middle_name:
            return f"{self.last_name} {self.first_name} {self.middle_name}"
        return f"{self.last_name} {self.first_name}"

    class Meta:
        verbose_name = "Водитель"
        verbose_name_plural = "Водители"


class Automobile(models.Model):
    make = models.CharField(max_length=50, verbose_name="Марка")
    model = models.CharField(max_length=50, verbose_name="Модель")
    license_plate = models.CharField(max_length=20, unique=True, verbose_name="Гос. номер")
    fuel_consumption_rate = models.FloatField(verbose_name="Норма расхода (л/100км)")
    current_mileage = models.FloatField(default=0, verbose_name="Текущий пробег (км)")

    inspection_due_date = models.DateField(verbose_name="Дата окончания техосмотра")
    insurance_due_date = models.DateField(verbose_name="Дата окончания страховки")

    last_updated = models.DateTimeField(auto_now=True, verbose_name="Последнее изменение")

    def __str__(self):
        return f"{self.make} {self.model} ({self.license_plate})"

    def is_inspection_due(self):
        days_left = (self.inspection_due_date - timezone.now().date()).days
        return days_left <= 30

    def is_insurance_due(self):
        days_left = (self.insurance_due_date - timezone.now().date()).days
        return days_left <= 30

    class Meta:
        verbose_name = "Автомобиль"
        verbose_name_plural = "Автомобили"


class TravelLog(models.Model):
    automobile = models.ForeignKey(Automobile, on_delete=models.CASCADE, verbose_name="Автомобиль")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, verbose_name="Водитель")

    log_number = models.CharField(max_length=50, default=get_next_log_number, verbose_name="Номер путевого листа")

    start_date = models.DateField(default=timezone.now, verbose_name="Дата начала поездки")
    departure_time = models.TimeField(verbose_name="Время выезда")

    end_date = models.DateField(default=timezone.now, verbose_name="Дата окончания поездки")
    return_time = models.TimeField(verbose_name="Время возвращения")

    start_mileage = models.FloatField(verbose_name="Показания спидометра при выезде")
    end_mileage = models.FloatField(verbose_name="Показания спидометра при возвращении")

    route = models.TextField(verbose_name="Маршрут следования")

    fuel_balance_start = models.FloatField(verbose_name="Остаток горючего при выезде")
    fuel_issued = models.FloatField(default=0, verbose_name="Выдано горючего")
    fuel_balance_end = models.FloatField(verbose_name="Остаток горючего при возвращении")

    def __str__(self):
        return f"Лист №{self.log_number} от {self.start_date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.end_mileage > self.automobile.current_mileage:
            self.automobile.current_mileage = self.end_mileage
            self.automobile.save()

    @property
    def distance_traveled(self):
        return self.end_mileage - self.start_mileage

    @property
    def normative_fuel(self):
        return (self.distance_traveled / 100) * self.automobile.fuel_consumption_rate

    @property
    def actual_fuel(self):
        return (self.fuel_balance_start + self.fuel_issued) - self.fuel_balance_end

    @property
    def economy_overrun(self):
        return self.normative_fuel - self.actual_fuel

    class Meta:
        verbose_name = "Путевой лист"
        verbose_name_plural = "Путевые листы"
        ordering = ['-start_date', '-id']
