from django.shortcuts import render
from django.views.generic import TemplateView
from .models import Product, Category


def index(request):
    return render(request, 'index.html')


class CatalogView(TemplateView):
    template_name = "catalog.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['products'] = Product.objects.all()
        return context
