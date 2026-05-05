from rest_framework import serializers
from django.db import transaction
from .models import Cliente, Venta, DetalleVenta
from inventario.models import Producto


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'telefono', 'email']


class DetalleVentaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = DetalleVenta
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio_unitario', 'subtotal']


class CrearDetalleSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1)


class CrearVentaSerializer(serializers.Serializer):
    cliente_id = serializers.IntegerField(required=False, allow_null=True)
    metodo_pago = serializers.ChoiceField(choices=['efectivo', 'tarjeta', 'transferencia'])
    notas = serializers.CharField(required=False, allow_blank=True)
    items = CrearDetalleSerializer(many=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError('La venta debe tener al menos un producto.')
        return items

    def validate(self, data):
        # Verificar stock suficiente para cada producto
        for item in data['items']:
            try:
                producto = Producto.objects.get(pk=item['producto_id'])
            except Producto.DoesNotExist:
                raise serializers.ValidationError(
                    f'Producto con id {item["producto_id"]} no existe.'
                )
            if producto.stock < item['cantidad']:
                raise serializers.ValidationError(
                    f'Stock insuficiente para "{producto.nombre}". '
                    f'Disponible: {producto.stock}, solicitado: {item["cantidad"]}.'
                )
        return data

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        items = validated_data.pop('items')
        cliente_id = validated_data.pop('cliente_id', None)

        venta = Venta.objects.create(
            cliente_id=cliente_id,
            vendedor=request.user if request else None,
            **validated_data
        )

        for item in items:
            producto = Producto.objects.get(pk=item['producto_id'])
            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                cantidad=item['cantidad'],
                precio_unitario=producto.precio,
            )

        return venta


class VentaSerializer(serializers.ModelSerializer):
    detalles = DetalleVentaSerializer(many=True, read_only=True)
    cliente = ClienteSerializer(read_only=True)
    vendedor_nombre = serializers.CharField(source='vendedor.username', read_only=True)

    class Meta:
        model = Venta
        fields = [
            'id', 'cliente', 'vendedor_nombre', 'metodo_pago',
            'estado', 'total', 'notas', 'detalles', 'creado_en'
        ]