from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.contrib import messages
from .utils import send_email_async
from random import randint

from django.utils import timezone
from datetime import timedelta

from .models import PendingUser, User
from orders.models import Order

# Create your views here.
"""Вью для страницы пользователя"""
class ProfileView(View):
    """Метод для отображения страницы пользователя"""
    def get(self, request):
        if not(request.user.is_authenticated):
            return redirect('register')

        user = request.user

        context = {
            'user': user,
            'orders': user.orders.all()
        }

        return render(request, 'profile.html', context)

    def post(self, request):
        if not(request.user.is_authenticated):
            return redirect('register')

        new_phone_number = request.POST.get('new_phone_number', '').strip()
        new_first_name = request.POST.get('new_first_name', '').strip()
        new_last_name = request.POST.get('new_last_name', '').strip()
        new_address = request.POST.get('new_address', '').strip()

        user = request.user

        # Обновляем только непустые поля
        if new_phone_number:
            # Базовая проверка телефона (только цифры и минимум 10 символов)
            clean_phone = ''.join(filter(str.isdigit, new_phone_number))
            if len(clean_phone) >= 10:
                user.phone_number = new_phone_number
            else:
                return redirect('profile')

        if new_first_name:
            if len(new_first_name) >= 2 and new_first_name.replace(' ', '').isalpha():
                user.first_name = new_first_name
            else:
                return redirect('profile')

        if new_last_name:
            if len(new_last_name) >= 2 and new_last_name.replace(' ', '').isalpha():
                user.last_name = new_last_name
            else:
                return redirect('profile')

        if new_address:
            if len(new_address) >= 5:
                user.address = new_address
            else:
                return redirect('profile')

        try:
            print(user.address)
            user.save()
        except Exception:
            pass

        return redirect('profile')


"""Вью для страницы регистрации"""
class RegisterView(View):

    """Метод для отображения страницы"""
    def get(self, request):
        return render(request, 'register.html')


    """Метод для обработки данных регистрации и отправки кода потверждения"""
    def post(self, request):
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        required_fields = [first_name, last_name, phone_number, email, password]

        if not all(required_fields):
            messages.error(request, 'Все поля обязательны для заполнения')
            return redirect('register')

        if password != confirm_password:
            return redirect('register')

        if len(password) < 8:
            # TODO: Можно добавить дополнительную проверку
            messages.error(request, 'Пароль должен содержать минимум 8 символов')
            return redirect('register')

        # Проверяем есть ли пользователь с таким email
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким email уже существует')
            return redirect('register')

        # Проверяем есть ли пользователь с таким номером
        if User.objects.filter(phone_number=phone_number).exists():
            messages.error(request, 'Пользователь с таким номером телефона уже существует')
            return redirect('register')

        # Создаем 6-значный код потверждения email
        verification_code = [randint(0,9) for num in range(6)]
        verification_code = ''.join(map(str, verification_code))

        # Удаляем старые попытки попытки регистрации с этим email
        PendingUser.objects.filter(email=email).delete()

        # Отправляем код потверждения на почту пользователя
        send_email_async(
            subject="Код для регистрации",
            message=f"{verification_code}\nНикому не сообщайте код",
            recipient=email,
        )

        # Сохраняем email пользователя в сессии для следующего этапа
        request.session['pending_email'] = email

        # Создаем временную запись пользователя
        PendingUser.objects.create(
            first_name = first_name,
            last_name = last_name,
            phone_number = phone_number,
            email = email,
            password = password,
            verification_code = verification_code
        )

        return redirect('confirm_email')


"""Вью для потверждения email"""
class ConfirmEmailView(View):

    """Метод для отображения страницы потверждения email"""
    def get(self, request):
        return render(request, 'email_confirm.html')


    """Метод для получения кода потверждения и его проверки"""
    def post(self, request):
        email = request.session.get('pending_email')
        verification_code = request.POST.get('verification_code')

        if not(email and verification_code):
            return redirect('register')

        # Достаем временную запись пользователя
        pending_user = PendingUser.objects.filter(email=email).last()

        if pending_user is None:
            return redirect('register')

        # Проверяем не истекло ли время потверждения
        time_passed = timezone.now() - pending_user.register_at

        if time_passed > timedelta(minutes=15):
            pending_user.delete()
            return redirect('register')

        # Проверяем код потверждения
        if pending_user.verification_code != verification_code:
            return redirect('confirm_email')

        phone_number = pending_user.phone_number
        first_name = pending_user.first_name
        last_name = pending_user.last_name
        password = pending_user.password

        # Проверяем не зарегистрирован ли такой пользователь
        if User.objects.filter(email=email).exists():
            return redirect('register') # TODO: Поставить другой url

        if User.objects.filter(phone_number=phone_number).exists():
            return redirect('register') # TODO: Поставить другой url

        # Создаем пользователя если проверки прошли
        user = User.objects.create_user(
            email = email,
            phone_number = phone_number,
            first_name = first_name,
            last_name = last_name,
            password = password
        )

        # Удаляем временную запись пользователя
        pending_user.delete()

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        return redirect('profile')


""" Вью для логина пользователей"""
class LoginView(View):
    # Метод для отображения страницы логина
    def get(self, request):
        return render(request, 'login.html')

    # Метод с логикой логина
    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not(email and  password):
            messages.error(request, "Укажите логин и пароль")
            return redirect('login')

        user = authenticate(request, email=email, password=password)

        if user is None:
            messages.error(request, 'Логин или пароль неверный')
            return redirect('login')

        login(request, user)
        return redirect('profile')


"""Вью для выхода пользователя"""
class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('home')
