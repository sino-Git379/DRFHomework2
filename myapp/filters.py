def price_filter(queryset, params):

    min_price = params.get("min_price")
    max_price = params.get("max_price")

    if min_price:
        queryset = queryset.filter(price__gte=min_price)
    if max_price:
        queryset = queryset.filter(price__lte=max_price)

    return queryset
