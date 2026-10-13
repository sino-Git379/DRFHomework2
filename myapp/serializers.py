from django.db.models import Avg
from rest_framework import serializers

from .models import Category, Product, Review, User


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ("id", "rating", "text")
        read_only_fields = ("id",)


class ProductSerializer(serializers.ModelSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)
    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True)
    owner_data = serializers.SerializerMethodField()
    category_data = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("id", "title", "description", "price", "category", "category_data", "owner", "owner_data", "created_at", "avg_rating", "review_count", "reviews")
        read_only_fields = ("id", "created_at", "owner_data", "category_data", "avg_rating", "review_count", "reviews")

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title must not be empty.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def get_owner_data(self, obj):
        return {"username": obj.owner.username}

    def get_category_data(self, obj):
        return {"name": obj.category.name}

    def get_avg_rating(self, obj):
        avg = obj.reviews.aggregate(value=Avg("rating"))["value"]
        return round(avg, 2) if avg is not None else None

    def get_review_count(self, obj):
        return obj.reviews.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Keep the average explicit in representation as requested.
        data["avg_rating"] = self.get_avg_rating(instance)
        return data


class ReviewCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Review
        fields = ("id", "rating", "text", "product", "user")
        read_only_fields = ("id", "product")

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, attrs):
        product = self.context["product"]
        user = attrs["user"]
        if Review.objects.filter(product=product, user=user).exists():
            raise serializers.ValidationError("You can leave only one review per product.")
        attrs["product"] = product
        attrs["user"] = user
        return attrs
