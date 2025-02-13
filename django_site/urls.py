"""
URL configuration for aiqa project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from rest_framework import permissions

class BothHttpAndHttpsSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ["https", "http", ]
        return schema

schema_view = get_schema_view(
    openapi.Info(
        title=settings.SWAGGER_SETTINGS.get("TITLE"),
        default_version=settings.SWAGGER_SETTINGS.get("VERSION"),
    ),
    url=getattr(settings, 'SWAGGER_SCHEMA_URL', None),
    generator_class=BothHttpAndHttpsSchemaGenerator,
    public=False,
    permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('chatRobot.urls')),  # Include all chatRobot routes under /api/v1/
    path('apidocs/', schema_view.with_ui('swagger', cache_timeout=0), name='apidocs'),
]
