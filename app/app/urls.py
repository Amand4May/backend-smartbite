from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="SmartBite API",
        default_version="v1",
        description="API do SmartBite — comedouro inteligente para pets",
        contact=openapi.Contact(email="contato@smartbite.com.br"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    # API v1
    path("api/v1/", include("smartbite.urls_api", namespace="smartbite-api")),
    # Swagger / ReDoc
    re_path(r"^api/docs/$", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    re_path(r"^api/redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    re_path(r"^api/docs/json/$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
]
