from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):

    def create_user(
        self,
        email,
        phone_number=None,
        first_name='',
        last_name='',
        address='',
        password=None,
        **extra_fields
    ):
        """
        Создание обычного пользователя
        """
        if not email:
            raise ValueError('Email обязателен')

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            address=address,
            **extra_fields,
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email,
        phone_number=None,
        first_name='',
        last_name='',
        address='',
        password=None,
        **extra_fields
    ):
        """
        Создание суперпользователя (для админки)
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(
            email=email,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            address=address,
            password=password,
            **extra_fields
        )