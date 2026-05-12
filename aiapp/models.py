from django.db import models

# Create your models here.
from django.db import models

class Dress(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="dresses/")

    def __str__(self):
        return self.name


class TryOn(models.Model):
    user_image = models.ImageField(upload_to="users/")
    dress = models.ForeignKey(Dress, on_delete=models.CASCADE)
    result_image = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)