from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import DetalleVenta


@receiver(post_save, sender=DetalleVenta)
def descontar_stock(sender, instance, created, **kwargs):
    if created:
        producto = instance.producto
        producto.stock -= instance.cantidad
        producto.save(update_fields=['stock'])
        # Recalcular total de la venta
        instance.venta.calcular_total()


@receiver(post_delete, sender=DetalleVenta)
def restaurar_stock(sender, instance, **kwargs):
    producto = instance.producto
    producto.stock += instance.cantidad
    producto.save(update_fields=['stock'])
    instance.venta.calcular_total()