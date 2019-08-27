from django.core import paginator
from rest_framework.pagination import PageNumberPagination


class MyPagination(PageNumberPagination):

    page_size = 20
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view=None)
        except Exception:
            # page_size = self.get_page_size(request)
            paginator = self.django_paginator_class(queryset, self.page_size)
            self.page = paginator.page(1)
            self.request = request
            return list(self.page)

    # def get_paginated_response(self, data):
    #     return super().get_paginated_response(data)

# 可以在子类中定义的属性：
# page_size 每页数目
# page_query_param 前端发送的页数关键字名，默认为"page"
# page_size_query_param 前端发送的每页数目关键字名，默认为None
# max_page_size 前端最多能设置的每页数量