from django.contrib import admin
from .models import Category, Product, Review, User

admin.site.register((Category, Product, Review, User))
