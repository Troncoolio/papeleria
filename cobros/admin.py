from django.contrib import admin
from .models import Cliente, Venta, DetalleVenta


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1
    readonly_fields = ['subtotal']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'telefono', 'email']
    search_fields = ['nombre', 'email']


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'vendedor', 'metodo_pago', 'total', 'estado', 'creado_en']
    list_filter = ['estado', 'metodo_pago', 'creado_en']
    readonly_fields = ['total', 'creado_en']
    inlines = [DetalleVentaInline]