import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Producto } from 'src/app/interface/producto.interface';
import { AlertasService } from 'src/app/services/alertas';
import { ServiceService } from 'src/app/services/service';
import { ActionSheetController, AlertController, ToastController } from '@ionic/angular';

@Component({
  selector: 'app-inventario',
  templateUrl: './inventario.page.html',
  styleUrls: ['./inventario.page.scss'],
  standalone: false
})
export class InventarioPage implements OnInit {
  searchTerm: string = '';
  productos: Producto[] = [];

  constructor(
    private router: Router,
    private service: ServiceService,
    private alertasService: AlertasService,
    private actionSheetCtrl: ActionSheetController,
    private toastCtrl: ToastController,
    private alertCtrl: AlertController
  ) {}

  ngOnInit(): void {
    this.cargarProductos();
  }

  ionViewWillEnter() {
    this.cargarProductos();
  }

  /* Helper: toast rápido (mensaje corto no bloqueante) */
  private async presentToast(message: string, color: 'success' | 'danger' | 'warning' | 'primary' = 'danger', duration = 2000) {
    const t = await this.toastCtrl.create({
      message,
      duration,
      color,
      position: 'top'
    });
    await t.present();
  }

  cargarProductos(): void {
    const token = localStorage.getItem('auth_token') || '';
    this.service.obtenerProductos(token).subscribe({
      next: (data) => {
        this.productos = data || [];
        this.alertasService?.refrescar?.();
      },
      error: async () => {
        await this.presentToast('No se pudieron cargar los productos', 'danger', 2200);
        this.router.navigate(['/login']);
      }
    });
  }

  onToggleStatus(event: any, producto: Producto) {
    const nuevoEstado = !!event.detail?.checked;
    producto.activo = nuevoEstado;
    this.cambiarStatus(producto);
  }

  cambiarStatus(producto: Producto) {
    const token = localStorage.getItem('auth_token') || '';
    const estadoNuevo = !!producto.activo;

    if (!producto.idProducto) {
      this.presentToast('Producto inválido', 'danger', 1800);
      return;
    }

    this.service.actualizarEstadoProducto(producto.idProducto, estadoNuevo, token).subscribe({
      next: async () => {
        this.alertasService?.refrescar?.();
        await this.presentToast('Status actualizado', 'success', 1200);
      },
      error: async () => {
        producto.activo = !estadoNuevo; // revertir
        await this.presentToast('No se pudo actualizar el status', 'danger', 1800);
      }
    });
  }

  productosFiltrados() {
    const term = this.searchTerm?.toLowerCase() || '';
    if (!term) return this.productos;
    return this.productos.filter(p => (p.nombre || '').toLowerCase().includes(term));
  }

  agregarProducto() {
    this.router.navigate(['/agregar']);
  }

  editarProducto(producto: Producto) {
    if (!producto?.idProducto) return;
    this.router.navigate(['/agregar', producto.idProducto]);
  }

  ajustarStock(producto: Producto) {
    if (!producto?.idProducto) return;
    this.router.navigate(['/stock', producto.idProducto]);
  }

  async eliminarProducto(producto: Producto) {
    if (!producto?.idProducto) return;

    // Pregunta de confirmación usando AlertController (nativo)
    const alert = await this.alertCtrl.create({
      header: `¿Eliminar ${producto.nombre}?`,
      message: 'Esta acción no se puede deshacer.',
      buttons: [
        {
          text: 'Cancelar',
          role: 'cancel'
        },
        {
          text: 'Sí, eliminar',
          cssClass: 'danger',
          handler: async () => {
            const token = localStorage.getItem('auth_token') || '';
            this.service.eliminarProducto(producto.idProducto!, token).subscribe({
              next: async () => {
                await this.presentToast('Producto eliminado', 'success', 1200);
                this.cargarProductos();
              },
              error: async () => {
                await this.presentToast('No se pudo eliminar el producto', 'danger', 1700);
              }
            });
          }
        }
      ]
    });

    await alert.present();
  }

  async openActions(producto: Producto) {
    // action sheet ya es nativo de Ionic; lo dejamos tal cual
    const actionSheet = await this.actionSheetCtrl.create({
      header: producto.nombre,
      buttons: [
        {
          text: 'Ajustar stock',
          icon: 'add',
          handler: () => { this.ajustarStock(producto as Producto); }
        },
        {
          text: 'Editar',
          icon: 'pencil',
          handler: () => { this.editarProducto(producto as Producto); }
        },
        {
          text: 'Eliminar',
          role: 'destructive',
          icon: 'trash',
          handler: () => { this.eliminarProducto(producto as Producto); }
        },
        {
          text: 'Cancelar',
          icon: 'close',
          role: 'cancel'
        }
      ]
    });

    await actionSheet.present();
  }
}
