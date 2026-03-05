"""URLs de la boutique.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InventoryViewSet, ShopViewSet

router = DefaultRouter()
router.register(r"items", ShopViewSet, basename="shop-item")
router.register(r"inventory", InventoryViewSet, basename="shop-inventory")

urlpatterns = [
    path("", include(router.urls)),
]
