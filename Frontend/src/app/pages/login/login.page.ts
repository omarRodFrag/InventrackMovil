import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AlertController, ToastController } from '@ionic/angular';
import { Login } from 'src/app/interface/login.interface';
import { ServiceService } from 'src/app/services/service';

@Component({
  selector: 'app-login',
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss'],
  standalone: false
})
export class LoginPage implements OnInit {
  loginForm!: FormGroup;
  showVerificationForm: boolean = false;
  isLoading: boolean = false;
  isVerifying: boolean = false;

  // Usamos tempToken hasta que el usuario verifique el código
  private tempTokenKey = 'temp_auth_token';
  private authTokenKey = 'auth_token';

  constructor(
    private fb: FormBuilder,
    private service: ServiceService,
    private router: Router,
    private toastCtrl: ToastController,
    private alertCtrl: AlertController
  ) {}

  ngOnInit(): void {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required]],
      verificationCode: [''] // Validador agregado dinámicamente cuando sea necesario
    });
  }

  // Helper: toast rápido (success | danger | warning | primary)
  private async presentToast(message: string, color: 'success' | 'danger' | 'warning' | 'primary' = 'danger', duration = 2000) {
    const toast = await this.toastCtrl.create({
      message,
      duration,
      color,
      position: 'top'
    });
    await toast.present();
  }

  // Helper: alert modal (cuando se necesita confirmación o mensaje largo)
  private async presentAlert(header: string, message?: string) {
    const alert = await this.alertCtrl.create({
      header,
      message,
      buttons: ['OK']
    });
    await alert.present();
  }

  login() {
    if (this.loginForm.invalid) {
      this.presentToast('Revisa los campos del formulario.', 'danger', 2200);
      return;
    }

    this.isLoading = true;

    const loginData: Login = {
      strEmail: this.loginForm.value.email,
      strPassword: this.loginForm.value.password,
    };

    this.service.login(loginData).subscribe({
      next: async (response: any) => {
        this.isLoading = false;
        // Esperamos token temporal del backend para usar en la verificación
        if (response?.message && response?.token) {
          // Guardamos en localStorage como temp hasta que verifiquen
          localStorage.setItem(this.tempTokenKey, response.token);
          await this.presentToast('Se envió el código de verificación a tu correo', 'success', 1800);
          this.showVerificationForm = true;

          // Hacemos required el campo verificationCode cuando aparece la sección
          const ctrl = this.loginForm.get('verificationCode');
          ctrl?.setValidators([Validators.required]);
          ctrl?.updateValueAndValidity();
        } else {
          await this.presentToast(response?.message || 'Respuesta inesperada del servidor', 'danger', 2200);
        }
      },
      error: async (error: any) => {
        this.isLoading = false;
        const mensaje =
          error.error?.error ||
          error.error?.message ||
          error.message ||
          'Ocurrió un error inesperado. Inténtalo de nuevo.';
        await this.presentToast(mensaje, 'danger', 2500);
      }
    });
  }

  verifyCode() {
    const codeCtrl = this.loginForm.get('verificationCode');
    if (codeCtrl?.invalid) {
      this.presentToast('Ingresa el código de verificación', 'danger', 1800);
      codeCtrl?.markAsTouched();
      return;
    }

    const code = codeCtrl?.value;
    const tempToken = localStorage.getItem(this.tempTokenKey) || '';

    if (!tempToken) {
      this.presentToast('Token temporal no encontrado. Vuelve a iniciar sesión.', 'danger', 2200);
      // Reset: esconder formulario de verificación por seguridad
      this.showVerificationForm = false;
      return;
    }

    this.isVerifying = true;

    this.service.verifyCode({ code }, tempToken).subscribe({
      next: async (response: any) => {
        this.isVerifying = false;
        if (response?.message === 'Código verificado correctamente' || /verificad/i.test(response?.message)) {
          // Mover temp token a token oficial (si tu backend maneja tokens finales distintos, ajusta aquí)
          // Si tu backend retorna un token final en esta respuesta, deberías usar ese token en vez de tempToken.
          localStorage.setItem(this.authTokenKey, tempToken);
          localStorage.removeItem(this.tempTokenKey);

          await this.presentToast('Código verificado correctamente', 'success', 1500);

          // Navegar a la app (ajusta la ruta)
          this.router.navigate(['/inventario']);
        } else {
          await this.presentToast(response?.message || 'Código incorrecto', 'danger', 2000);
        }
      },
      error: async (error: any) => {
        this.isVerifying = false;
        const mensaje =
          error.error?.error ||
          error.error?.message ||
          error.message ||
          'Hubo un problema al verificar el código';
        await this.presentToast(mensaje, 'danger', 2200);
      }
    });
  }
}
