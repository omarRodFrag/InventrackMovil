import { Component, OnInit } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import Swal from 'sweetalert2';
import { Observable } from 'rxjs';
import { IonicModule } from '@ionic/angular';
import { CommonModule } from '@angular/common';
import { AlertasService } from 'src/app/services/alertas';
import { AlertController } from '@ionic/angular';

@Component({
  selector: 'app-navbar',
  standalone: false,
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.scss']
})
export class NavbarComponent implements OnInit {
  alertasCount$!: Observable<number>;

  constructor(
    private alertasService: AlertasService,
    private router: Router,
    private alertCtrl: AlertController
  ) {}

  ngOnInit(): void {
    this.alertasCount$ = this.alertasService.alertasCount$;
    this.alertasService.refrescar();
  }

  /** Pregunta y cierra sesión */
  async confirmLogout() {
  const alert = await this.alertCtrl.create({
    header: 'Cerrar sesión',
    message: '¿Seguro que quieres salir?',
    buttons: [
      { text: 'Cancelar', role: 'cancel' },
      {
        text: 'Salir',
        handler: () => {
          localStorage.removeItem('auth_token');
          this.router.navigate(['/login']);
        }
      }
    ]
  });
  await alert.present();
}
}
