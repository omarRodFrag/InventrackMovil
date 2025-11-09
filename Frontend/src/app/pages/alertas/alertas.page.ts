import { Component, OnInit } from '@angular/core';
import { Producto } from 'src/app/interface/producto.interface';
import { ServiceService } from 'src/app/services/service';

@Component({
  selector: 'app-alertas',
  templateUrl: './alertas.page.html',
  styleUrls: ['./alertas.page.scss'],
  standalone: false
})
export class AlertasPage implements OnInit {
  alertas: Producto[] = [];

  constructor(private service: ServiceService) {}

  ngOnInit(): void {
    const token = localStorage.getItem('auth_token')!;
    this.service.obtenerProductos(token).subscribe({
      next: (productos) => {
        this.alertas = productos.filter(p => p.cantidad <= p.stockMinimo && p.activo);
      }
    });
  }
}
