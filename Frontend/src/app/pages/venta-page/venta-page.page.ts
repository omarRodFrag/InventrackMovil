import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AlertController } from '@ionic/angular';
import { ServiceService } from 'src/app/services/service';

@Component({
  selector: 'app-venta-page',
  templateUrl: './venta-page.page.html',
  styleUrls: ['./venta-page.page.scss'],
  standalone: false
})
export class VentaPagePage implements OnInit {

  ventaForm!: FormGroup;
  resultadoVenta: any = null;

  constructor(
    private fb: FormBuilder,
    private service: ServiceService,
    private router: Router,
    private alertCtrl: AlertController
  ) {}

  ngOnInit(): void {
    this.ventaForm = this.fb.group({
      nombre: ['', Validators.required],
      cantidad: [1, [Validators.required, Validators.min(1)]]
    });
  }

  async mostrarAlerta(header: string, message: string) {
    const alert = await this.alertCtrl.create({
      header,
      message,
      buttons: ['OK']
    });
    await alert.present();
  }

  procesarVenta(): void {
    if (this.ventaForm.invalid) {
      this.mostrarAlerta('Formulario inválido', 'Revisa los campos');
      return;
    }

    const token = localStorage.getItem('auth_token')!;
    if (!token) {
      this.mostrarAlerta('No autorizado', 'Inicia sesión primero');
      return;
    }

    const payload = {
      nombre: this.ventaForm.value.nombre,
      cantidad: this.ventaForm.value.cantidad
    };

    this.service.ventaPorNombre(payload, token).subscribe({
      next: (res: any) => {
        // Respuesta esperada: { message: 'Venta procesada correctamente', producto: { ... } }
        this.resultadoVenta = res;
        this.mostrarAlerta('Éxito', 'Venta procesada correctamente');
      },
      error: async (err) => {
        // Maneja errores tal como haces en el resto del app
        let msg = 'Error al procesar la venta';
        if (err?.error?.error) msg = err.error.error;
        await this.mostrarAlerta('Error', msg);
      }
    });
  }

  cancelar(): void {
    this.router.navigate(['/inventario']);
  }

  nuevaVenta(): void {
    this.resultadoVenta = null;
    this.ventaForm.reset({ nombre: '', cantidad: 1 });
  }

  imprimirTicket(): void {
    // Placeholder simple. Si quieres generar PDF/guardar, lo añadimos.
    const prod = this.resultadoVenta?.producto;
    if (!prod) {
      this.mostrarAlerta('Nada que imprimir', 'No hay ticket disponible');
      return;
    }
    const texto = `Ticket\nProducto: ${prod.nombre}\nID: ${prod.idProducto}\nStock restante: ${prod.cantidad}`;
    // Por ahora mostramos en alert (o copiar al clipboard si quieres)
    this.mostrarAlerta('Ticket (copiar)', texto.replace(/\n/g,'<br/>'));
  }
}
