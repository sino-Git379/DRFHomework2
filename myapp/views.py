from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product
from .filters import price_filter
from .pagination import CustomPagination
from .serializers import ProductSerializer, ReviewCreateSerializer


@api_view(["GET", "POST"])
def product_list(request):
    if request.method == "GET":
        products = Product.objects.select_related("category", "owner").prefetch_related("reviews").all()
        category = request.query_params.get("category")
        if category:
            products = products.filter(category_id=category)
        products = price_filter(products, request.GET)
        search = request.GET.get("search")
        if search:
            products = products.filter(title__icontains=search)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    serializer = ProductSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    product = serializer.save()
    return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def product_detail(request, pk):
    try:
        product = Product.objects.select_related("category", "owner").prefetch_related("reviews").get(pk=pk)
    except Product.DoesNotExist:
        return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response(ProductSerializer(product).data)
    user_id = request.data.get("owner", request.query_params.get("user_id"))
    if str(product.owner_id) != str(user_id):
        return Response({"detail": "You may only modify or delete your own products."}, status=status.HTTP_403_FORBIDDEN)
    if request.method == "DELETE":
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = ProductSerializer(product, data=request.data, partial=request.method == "PATCH")
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
def product_review_create(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer = ReviewCreateSerializer(data=request.data, context={"request": request, "product": product})
    serializer.is_valid(raise_exception=True)
    review = serializer.save()
    return Response({"id": review.id, "rating": review.rating, "text": review.text}, status=status.HTTP_201_CREATED)
