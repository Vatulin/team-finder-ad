from django.core.paginator import Paginator


def paginate_queryset(request, queryset, per_page=12):
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get("page"))

    query_params = request.GET.copy()
    query_params.pop("page", None)
    query_string = query_params.urlencode()

    return {
        "page_obj": page_obj,
        "query_prefix": f"{query_string}&" if query_string else "",
    }