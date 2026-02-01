from allauth.socialaccount.forms import SignupForm

class CustomSocialSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Удаляем поле username, если оно есть
        if 'username' in self.fields:
            del self.fields['username']