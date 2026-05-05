from django.urls import path
from . import views

urlpatterns = [
    path('caja/', views.caja, name='caja'),
    path('reportes/', views.reportes, name='reportes'),  

    path('api/cobros/clientes/', views.ClienteListAPIView.as_view(), name='api-clientes'),
    path('api/cobros/ventas/', views.VentaListAPIView.as_view(), name='api-ventas'),
    path('api/cobros/venta/crear/', views.CrearVentaAPIView.as_view(), name='api-crear-venta'),
    path('api/cobros/resumen/', views.ResumenDiaAPIView.as_view(), name='api-resumen'),
    path('api/cobros/reportes/', views.ReporteVentasAPIView.as_view(), name='api-reportes'), 
    path('ticket/<int:pk>/', views.ticket, name='ticket'),
]