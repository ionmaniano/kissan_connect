from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        FARMER = "FARMER", "Farmer"
        BUYER = "BUYER", "Buyer"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
