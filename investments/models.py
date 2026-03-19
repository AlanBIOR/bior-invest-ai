from django.db import models
from django.contrib.auth.models import User

class Investment(models.Model):
    # Categorías exactas de tu captura de pantalla
    CATEGORY_CHOICES = [
        ('RV', 'Renta Variable'),
        ('IN', 'Inmuebles'),
        ('PE', 'Private Equity'),
        ('IA', 'Inversiones Alternativas'),
        ('EF', 'Efectivo'),
        ('RF', 'Renta Fija'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=2, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    # Este campo es vital para el Chatbot de IA
    description = models.TextField(blank=True, help_text="Notas para el análisis de la IA")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_category_display()} - ${self.amount}"