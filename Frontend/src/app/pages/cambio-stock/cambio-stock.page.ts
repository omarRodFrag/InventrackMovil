import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AlertController } from '@ionic/angular';
import { AlertasService } from 'src/app/services/alertas';
import { ServiceService } from 'src/app/services/service';


@Component({
  selector: 'app-cambio-stock',
  templateUrl: './cambio-stock.page.html',
  styleUrls: ['./cambio-stock.page.scss'],
  standalone: false
})
export class CambioStockPage implements OnInit {

  stockForm!: FormGroup;
  productoId!: string;

  constructor(
    private fb: FormBuilder,
    private service: ServiceService,
    private route: ActivatedRoute,
    private alertasService: AlertasService,
    private router: Router,
    private alertCtrl: AlertController
  ) {}

  ngOnInit(): void {
    this.stockForm = this.fb.group({
      cantidad: [0, [Validators.required, Validators.min(0)]],
      stockMinimo: [0, [Validators.required, Validators.min(0)]]
    });

    this.productoId = this.route.snapshot.paramMap.get('id')!;
    const token = localStorage.getItem('auth_token')!;
    this.service.obtenerProductoPorId(this.productoId, token).subscribe({
      next: (producto) => {
        this.stockForm.patchValue({
          cantidad: producto.cantidad,
          stockMinimo: producto.stockMinimo
        });
      },
      error: async () => {
        const alert = await this.alertCtrl.create({
          header: 'Error',
          message: 'No se pudo cargar el stock',
          buttons: ['OK']
        });
        await alert.present();
        this.router.navigate(['/inventario']);
      }
    });
  }

  guardar(): void {
    if (this.stockForm.invalid) {
      this.stockForm.markAllAsTouched();
      return;
    }

    const token = localStorage.getItem('auth_token')!;
    this.service.actualizarProducto(this.productoId, this.stockForm.value, token)
      .subscribe({
        next: async () => {
          this.alertasService.refrescar();
          const alert = await this.alertCtrl.create({
            header: 'Éxito',
            message: 'Stock actualizado correctamente',
            buttons: ['OK']
          });
          await alert.present();
          this.router.navigate(['/inventario']);
        },
        error: async () => {
          const alert = await this.alertCtrl.create({
            header: 'Error',
            message: 'No se pudo actualizar el stock',
            buttons: ['OK']
          });
          await alert.present();
        }
      });
  }

  cancelar(): void {
    this.router.navigate(['/inventario']);
  }

  get c() { return this.stockForm.controls; }

}
