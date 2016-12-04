from django.db import models


class Perashok(models.Model):
    perashok_text = models.CharField(max_length=1000)
    adding_date = models.DateTimeField('date saved')

