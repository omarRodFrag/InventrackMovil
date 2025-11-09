import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AlertController } from '@ionic/angular';
import { ServiceService } from 'src/app/services/service';

@Component({
  selector: 'app-agregar-producto',
  templateUrl: './agregar-producto.page.html',
  styleUrls: ['./agregar-producto.page.scss'],
  standalone: false
})
export class AgregarProductoPage implements OnInit {

  productoForm!: FormGroup;
  modoEdicion: boolean = false;
  productoId: string | null = null;

  constructor(
    private fb: FormBuilder,
    private service: ServiceService,
    private route: ActivatedRoute,
    private router: Router,
    private alertCtrl: AlertController
  ) {}

  ngOnInit(): void {
    this.productoForm = this.fb.group({
      nombre: ['', Validators.required],
      categoria: ['', Validators.required],
      descripcion: [''],
      cantidad: [0, [Validators.required, Validators.min(0)]],
      stockMinimo: [0, [Validators.required, Validators.min(0)]],
      activo: [true]
    });

    this.productoId = this.route.snapshot.paramMap.get('id');
    this.modoEdicion = !!this.productoId;

    if (this.modoEdicion && this.productoId) {
      const token = localStorage.getItem('auth_token')!;
      this.service.obtenerProductoPorId(this.productoId, token).subscribe({
        next: (producto) => this.productoForm.patchValue(producto),
        error: async () => {
          await this.mostrarAlerta('Error', 'No se pudo cargar el producto.');
          this.router.navigate(['/inventario']);
        }
      });
    }
  }

  async mostrarAlerta(header: string, message: string) {
    const alert = await this.alertCtrl.create({
      header,
      message,
      buttons: ['OK']
    });
    await alert.present();
  }

  guardar(): void {
    if (this.productoForm.invalid) {
      this.mostrarAlerta('Formulario inválido', 'Revisa los campos');
      return;
    }

    const token = localStorage.getItem('auth_token')!;
    const producto = this.productoForm.value;

    if (this.modoEdicion && this.productoId) {
      this.service.actualizarProducto(this.productoId, producto, token).subscribe({
        next: async () => {
          await this.mostrarAlerta('Actualizado', 'Producto actualizado correctamente');
          this.router.navigate(['/inventario']);
        },
        error: async () => {
          await this.mostrarAlerta('Error', 'No se pudo actualizar el producto');
        }
      });
    } else {
      this.service.agregarProducto(producto, token).subscribe({
        next: async () => {
          await this.mostrarAlerta('Agregado', 'Producto agregado correctamente');
          this.router.navigate(['/inventario']);
        },
        error: async () => {
          await this.mostrarAlerta('Error', 'No se pudo agregar el producto');
        }
      });
    }
  }

  cancelar(): void {
    this.router.navigate(['/inventario']);
  }

}
