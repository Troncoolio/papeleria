from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.db import models as db_models
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Cliente, Venta
from .serializers import ClienteSerializer, VentaSerializer, CrearVentaSerializer
from django.shortcuts import get_object_or_404

class ClienteListAPIView(generics.ListCreateAPIView):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]


class VentaListAPIView(generics.ListAPIView):
    serializer_class = VentaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Venta.objects.prefetch_related('detalles__producto').select_related('cliente')


class CrearVentaAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CrearVentaSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            venta = serializer.save()
            return Response(
                VentaSerializer(venta).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResumenDiaAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        hoy = timezone.now().date()
        ventas_hoy = Venta.objects.filter(
            creado_en__date=hoy,
            estado='completada'
        )
        total = ventas_hoy.aggregate(total=Sum('total'))['total'] or 0
        cantidad = ventas_hoy.count()

        return Response({
            'fecha': hoy,
            'total_vendido': total,
            'numero_ventas': cantidad,
        })


@login_required
def caja(request):
    return render(request, 'cobros/caja.html')


@login_required
def reportes(request):
    return render(request, 'cobros/reportes.html')


class ReporteVentasAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        periodo = request.query_params.get('periodo', 'dia')
        hoy = timezone.now().date()

        if periodo == 'dia':
            fecha_inicio = hoy
        elif periodo == 'semana':
            fecha_inicio = hoy - timedelta(days=7)
        elif periodo == 'mes':
            fecha_inicio = hoy - timedelta(days=30)
        else:
            fecha_inicio = hoy

        ventas = Venta.objects.filter(
            creado_en__date__gte=fecha_inicio,
            estado='completada'
        )

        resumen = ventas.aggregate(
            total=Sum('total'),
            cantidad=Count('id')
        )

        por_dia = (
            ventas
            .annotate(dia=TruncDate('creado_en'))
            .values('dia')
            .annotate(total=Sum('total'), cantidad=Count('id'))
            .order_by('dia')
        )

        from cobros.models import DetalleVenta
        top_productos = (
            DetalleVenta.objects
            .filter(venta__in=ventas)
            .values('producto__nombre')
            .annotate(
                total_vendido=Sum('cantidad'),
                ingresos=Sum(
                    db_models.ExpressionWrapper(
                        db_models.F('cantidad') * db_models.F('precio_unitario'),
                        output_field=db_models.DecimalField()
                    )
                )
            )
            .order_by('-total_vendido')[:5]
        )

        por_metodo = (
            ventas
            .values('metodo_pago')
            .annotate(total=Sum('total'), cantidad=Count('id'))
        )

        return Response({
            'periodo': periodo,
            'fecha_inicio': fecha_inicio,
            'resumen': {
                'total': resumen['total'] or 0,
                'cantidad': resumen['cantidad'] or 0,
            },
            'por_dia': list(por_dia),
            'top_productos': list(top_productos),
            'por_metodo': list(por_metodo),
        })

@login_required
def ticket(request, pk):
    venta = get_object_or_404(
        Venta.objects.prefetch_related('detalles__producto').select_related('cliente'),
        pk=pk
    )
    return render(request, 'cobros/ticket.html', {'venta': venta})