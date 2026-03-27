from django import forms
from django.contrib.auth.models import User
from .models import Profile

class RegistroForm(forms.ModelForm):
    # Campos adicionales que no están en el modelo User por defecto
    first_name = forms.CharField(label="Nombre", max_length=150, required=True)
    last_name = forms.CharField(label="Apellidos", max_length=150, required=True)
    whatsapp_number = forms.CharField(label="WhatsApp", max_length=20, required=True, help_text="Ej: 5212411234567")
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput, min_length=8)
    password2 = forms.CharField(label="Confirmar Contraseña", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd.get('password1') != cd.get('password2'):
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cd.get('password2')