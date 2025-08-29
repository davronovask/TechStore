from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterView(TemplateView):
    template_name = "register.html"

    def post(self, request, *args, **kwargs):
        nickname = request.POST.get("nickname")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirmPassword")

        # проверки
        if not nickname or len(nickname) < 3:
            return self.render_to_response({"error": "Никнейм слишком короткий!"})

        if not email.endswith("@gmail.com"):
            return self.render_to_response({"error": "Email должен быть @gmail.com"})

        if password != confirm_password or len(password) < 6:
            return self.render_to_response({"error": "Пароли не совпадают или слишком короткие!"})

        if User.objects.filter(username=nickname).exists():
            return self.render_to_response({"error": "Такой никнейм уже занят!"})

        if User.objects.filter(email=email).exists():
            return self.render_to_response({"error": "Такой email уже зарегистрирован!"})

        # создаем пользователя
        user = User.objects.create_user(username=nickname, email=email, password=password)
        login(request, user)  # сразу логиним
        return redirect("home")

class LoginView(TemplateView):
    template_name = "login.html"

    def post(self, request, *args, **kwargs):
        nickname = request.POST.get('nickname')
        password = request.POST.get('password')
        context = self.get_context_data(**kwargs)

        user = authenticate(request, username=nickname, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            context['error'] = "Неверный никнейм или пароль"
            return self.render_to_response(context)