from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import UserManager

# Create your models here.
"""Модель пользователя"""
class User(AbstractUser):
    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    objects = UserManager()


class PendingUser(models.Model):
    """
    Временное хранение данных пользователей до подтверждения email.

    Удаляется после успешной регистрации или истечения 15 минут.
    """
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255)

    # 6-значный код подтверждения
    verification_code = models.CharField(max_length=6, blank=True, null=True)

    # Время создания для проверки истечения срока
    register_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ожидающий пользователь"
        verbose_name_plural = "Ожидающие пользователи"
        ordering = ['-register_at']