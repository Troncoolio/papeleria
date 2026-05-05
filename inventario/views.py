from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Producto, Categoria
from rest_framework import generics, permissions
from .serializers import CategoriaSerializer, ProductoSerializer


def lista_productos(request):
    productos = Producto.objects.select_related('categoria').all()
    categorias = Categoria.objects.all()

    # Filtro por categoría
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    # Búsqueda por nombre
    q = request.GET.get('q')
    if q:
        productos = productos.filter(nombre__icontains=q)

    return render(request, 'inventario/lista.html', {
        'productos': productos,
        'categorias': categorias,
        'categoria_id': categoria_id,
        'q': q or '',
    })


def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'inventario/detalle.html', {'producto': producto})


@login_required
def crear_producto(request):
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        precio = request.POST.get('precio')
        stock = request.POST.get('stock', 0)
        categoria_id = request.POST.get('categoria') or None

        Producto.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            categoria_id=categoria_id,
        )
        messages.success(request, f'Producto "{nombre}" creado correctamente.')
        return redirect('lista_productos')

    return render(request, 'inventario/form.html', {
        'categorias': categorias,
        'accion': 'Crear',
    })


@login_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        producto.nombre = request.POST.get('nombre')
        producto.descripcion = request.POST.get('descripcion', '')
        producto.precio = request.POST.get('precio')
        producto.stock = request.POST.get('stock', 0)
        producto.categoria_id = request.POST.get('categoria') or None
        producto.save()
        messages.success(request, f'Producto "{producto.nombre}" actualizado.')
        return redirect('lista_productos')

    return render(request, 'inventario/form.html', {
        'producto': producto,
        'categorias': categorias,
        'accion': 'Editar',
    })


@login_required
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre}" eliminado.')
        return redirect('lista_productos')
    return render(request, 'inventario/confirmar_eliminar.html', {'producto': producto})




class CategoriaListAPIView(generics.ListCreateAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ProductoListAPIView(generics.ListCreateAPIView):
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Producto.objects.select_related('categoria').all()
        q = self.request.query_params.get('q')
        categoria_id = self.request.query_params.get('categoria')
        if q:
            qs = qs.filter(nombre__icontains=q)
        if categoria_id:
            qs = qs.filter(categoria_id=categoria_id)
        return qs


class ProductoDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Producto.objects.select_related('categoria').all()
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]