from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, date
from django.contrib.auth.models import User
from .models import Automobile, Driver, TravelLog, UserProfile, get_next_log_number
from .forms import TravelLogForm


class AutomobileModelTest(TestCase):
    def setUp(self):
        self.car = Automobile.objects.create(
            make="Toyota",
            model="Camry",
            license_plate="1234 AB-7",
            fuel_consumption_rate=10.0,
            current_mileage=1000,
            inspection_due_date=timezone.now().date() + timedelta(days=60),
            insurance_due_date=timezone.now().date() + timedelta(days=10)
        )

    def test_create_automobile(self):
        """Тест: Корректное создание автомобиля (Позитивный)"""
        self.assertEqual(self.car.make, "Toyota")
        self.assertEqual(self.car.current_mileage, 1000)

    def test_automobile_str(self):
        """Тест: Строковое представление автомобиля"""
        self.assertEqual(str(self.car), "Toyota Camry (1234 AB-7)")

    def test_is_inspection_due_positive(self):
        """Тест: Уведомление о техосмотре - срок подходит (Позитивный)"""
        self.car.inspection_due_date = timezone.now().date() + timedelta(days=5)
        self.assertTrue(self.car.is_inspection_due())

    def test_is_inspection_due_negative(self):
        """Тест: Уведомление о техосмотре - срок еще не подошел (Негативный)"""
        self.car.inspection_due_date = timezone.now().date() + timedelta(days=40)
        self.assertFalse(self.car.is_inspection_due())

    def test_is_insurance_due_positive(self):
        """Тест: Уведомление о страховке - срок подходит (Позитивный)"""
        self.assertTrue(self.car.is_insurance_due())

    def test_is_insurance_due_negative(self):
        """Тест: Уведомление о страховке - срок еще не подошел (Негативный)"""
        self.car.insurance_due_date = timezone.now().date() + timedelta(days=35)
        self.assertFalse(self.car.is_insurance_due())

    def test_search_automobile_by_plate(self):
        """Тест: Поиск автомобиля по гос. номеру"""
        found_cars = Automobile.objects.filter(license_plate__icontains="1234")
        self.assertEqual(found_cars.count(), 1)
        self.assertEqual(found_cars.first(), self.car)


class DriverModelTest(TestCase):
    def test_create_driver(self):
        """Тест: Создание водителя с полным ФИО"""
        driver = Driver.objects.create(
            last_name="Иванов",
            first_name="Иван",
            middle_name="Иванович",
            contact_info="+375290000000"
        )
        self.assertEqual(str(driver), "Иванов Иван Иванович")

    def test_create_driver_without_middle_name(self):
        """Тест: Создание водителя без отчества (Граничный случай)"""
        driver = Driver.objects.create(
            last_name="Петров",
            first_name="Петр",
            contact_info="+375291111111"
        )
        self.assertEqual(str(driver), "Петров Петр")


class TravelLogModelTest(TestCase):
    def setUp(self):
        self.car = Automobile.objects.create(
            make="Audi",
            model="A6",
            license_plate="5678 XX-7",
            fuel_consumption_rate=12.0,
            current_mileage=500,
            inspection_due_date=timezone.now().date() + timedelta(days=100),
            insurance_due_date=timezone.now().date() + timedelta(days=100)
        )
        self.driver = Driver.objects.create(last_name="Сидоров", first_name="Сидр", contact_info="N/A")

        self.log = TravelLog.objects.create(
            automobile=self.car,
            driver=self.driver,
            departure_time="08:00",
            return_time="17:00",
            start_mileage=500,
            end_mileage=600,
            fuel_balance_start=20,
            fuel_issued=10,
            fuel_balance_end=15,
            route="Test Route"
        )

    def test_travel_log_str(self):
        """Тест: Строковое представление путевого листа"""
        expected_str = f"Лист №{self.log.log_number} от {self.log.start_date}"
        self.assertEqual(str(self.log), expected_str)

    def test_distance_calculation(self):
        """Тест: Автоматический расчет пройденного расстояния"""
        self.assertEqual(self.log.distance_traveled, 100)

    def test_distance_calculation_zero(self):
        """Тест: Расчет расстояния при нулевом пробеге (Граничный случай)"""
        self.log.end_mileage = 500
        self.assertEqual(self.log.distance_traveled, 0)

    def test_normative_fuel_calculation(self):
        """Тест: Расчет нормативного расхода топлива"""
        expected_norm = (100 / 100) * 12.0
        self.assertEqual(self.log.normative_fuel, expected_norm)

    def test_actual_fuel_calculation(self):
        """Тест: Расчет фактического расхода топлива"""
        expected_actual = (20 + 10) - 15
        self.assertEqual(self.log.actual_fuel, expected_actual)

    def test_economy_overrun_calculation(self):
        """Тест: Расчет экономии или перерасхода"""
        norm = 12.0
        actual = 15.0
        expected = norm - actual
        self.assertEqual(self.log.economy_overrun, expected)

    def test_mileage_update_on_save(self):
        """Тест: Автоматическое обновление пробега авто при сохранении листа"""
        self.car.refresh_from_db()
        self.assertEqual(self.car.current_mileage, 600)

    def test_mileage_no_update_negative(self):
        """Тест: Пробег НЕ обновляется, если введены старые данные (Негативный)"""
        old_mileage = self.car.current_mileage
        TravelLog.objects.create(
            automobile=self.car,
            driver=self.driver,
            departure_time="10:00",
            return_time="12:00",
            start_mileage=100,
            end_mileage=200,
            fuel_balance_start=10,
            fuel_balance_end=5,
            route="Old Trip"
        )
        self.car.refresh_from_db()
        self.assertEqual(self.car.current_mileage, old_mileage)


class FormValidationTest(TestCase):
    def setUp(self):
        self.car = Automobile.objects.create(
            make="Test", model="Auto", license_plate="0000", fuel_consumption_rate=5,
            current_mileage=100, inspection_due_date=timezone.now().date(), insurance_due_date=timezone.now().date()
        )
        self.driver = Driver.objects.create(last_name="Test", first_name="Driver", contact_info="C")

    def test_log_form_valid(self):
        """Тест: Валидация формы путевого листа (Корректные данные)"""
        form_data = {
            'automobile': self.car.pk,
            'driver': self.driver.pk,
            'log_number': '100',
            'start_date': timezone.now().date(),
            'departure_time': '08:00',
            'end_date': timezone.now().date(),
            'return_time': '10:00',
            'start_mileage': 100,
            'end_mileage': 150,
            'fuel_balance_start': 10,
            'fuel_issued': 0,
            'fuel_balance_end': 5,
            'route': 'Test'
        }
        form = TravelLogForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_log_form_invalid_mileage(self):
        """Тест: Валидация формы - Конечный пробег меньше начального (Негативный)"""
        form_data = {
            'automobile': self.car.pk,
            'driver': self.driver.pk,
            'log_number': '100',
            'start_date': timezone.now().date(),
            'departure_time': '08:00',
            'end_date': timezone.now().date(),
            'return_time': '10:00',
            'start_mileage': 200,
            'end_mileage': 100,  # Ошибка
            'fuel_balance_start': 10,
            'fuel_issued': 0,
            'fuel_balance_end': 5,
            'route': 'Test'
        }
        form = TravelLogForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('end_mileage', form.errors)


class UtilsTest(TestCase):
    def test_get_next_log_number_initial(self):
        """Тест: Генерация номера первого путевого листа"""
        TravelLog.objects.all().delete()
        self.assertEqual(get_next_log_number(), "1")

    def test_get_next_log_number_increment(self):
        """Тест: Автоинкремент номера путевого листа"""
        car = Automobile.objects.create(
            make="Test", model="T", license_plate="0000", fuel_consumption_rate=5,
            current_mileage=0, inspection_due_date=timezone.now().date(), insurance_due_date=timezone.now().date()
        )
        driver = Driver.objects.create(last_name="D", first_name="D", contact_info="C")

        TravelLog.objects.create(
            log_number="5",
            automobile=car, driver=driver, departure_time="00:00", return_time="00:00",
            start_mileage=0, end_mileage=10, fuel_balance_start=0, fuel_balance_end=0
        )

        self.assertEqual(get_next_log_number(), "6")


class UserProfileSignalTest(TestCase):
    def test_profile_created_on_user_creation(self):
        """Тест: Автосоздание профиля сотрудника при регистрации"""
        user = User.objects.create_user(username='testuser', password='password')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_profile_default_values(self):
        """Тест: Проверка дефолтных значений профиля"""
        user = User.objects.create_user(username='testuser2', password='password')
        self.assertIsNone(user.profile.middle_name)
        self.assertEqual(user.profile.phone_number, '')

    def test_profile_update(self):
        """Тест: Обновление данных профиля"""
        user = User.objects.create_user(username='testuser3', password='password')
        user.profile.phone_number = "+123456789"
        user.profile.save()
        user.refresh_from_db()
        self.assertEqual(user.profile.phone_number, "+123456789")