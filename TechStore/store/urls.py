from django.urls import path
from store.views import HomePageView, CatalogView, DetailProductView, FavoritesView, CartView, OfferView, AboutView, \
    AddToCartView, UpdateCartItemView, ClearCartView, ToggleFavoriteView, PrivacyPolicyView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('favorites/', FavoritesView.as_view(), name='favorites'),
    path('favorites/toggle/<int:product_id>/', ToggleFavoriteView.as_view(), name='toggle_favorite'),
    path('cart/', CartView.as_view(), name='cart'),
    path('add/', AddToCartView.as_view(), name='add_to_cart'),
    path('update/<int:pk>/', UpdateCartItemView.as_view(), name='update_cart_item'),
    path('cart/clear/', ClearCartView.as_view(), name='clear_cart'),
    path('offer/', OfferView.as_view(), name='offer'),
    path('about/', AboutView.as_view(), name='about'),
    path('category/<slug:slug>/', CatalogView.as_view(), name='category'),
    path('product/<slug:slug>/', DetailProductView.as_view(), name='product_detail'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
]