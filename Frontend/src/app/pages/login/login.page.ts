import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import Swal from 'sweetalert2';
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
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required]],
      verificationCode: [''] // Validador agregado dinámicamente cuando sea necesario
    });
  }

  login() {
    if (this.loginForm.invalid) {
      Swal.fire({
        icon: 'error',
        title: 'Revisa los campos del formulario.',
        showConfirmButton: false,
        timer: 2200,
      });
      return;
    }

    this.isLoading = true;

    const loginData: Login = {
      strEmail: this.loginForm.value.email,
      strPassword: this.loginForm.value.password,
    };

    this.service.login(loginData).subscribe({
      next: (response: any) => {
        this.isLoading = false;
        // Esperamos token temporal del backend para usar en la verificación
        if (response?.message && response?.token) {
          // Guardamos en localStorage como temp hasta que verifiquen
          localStorage.setItem(this.tempTokenKey, response.token);
          Swal.fire({
            icon: 'success',
            title: 'Se envió el código de verificación a tu correo',
            showConfirmButton: false,
            timer: 1800,
          });
          this.showVerificationForm = true;

          // Hacemos required el campo verificationCode cuando aparece la sección
          const ctrl = this.loginForm.get('verificationCode');
          ctrl?.setValidators([Validators.required]);
          ctrl?.updateValueAndValidity();
        } else {
          Swal.fire({
            icon: 'error',
            title: 'Respuesta inesperada del servidor',
            text: response?.message || 'Sin token recibido',
            showConfirmButton: false,
            timer: 2200,
          });
        }
      },
      error: (error: any) => {
        this.isLoading = false;
        const mensaje =
          error.error?.error ||
          error.error?.message ||
          error.message ||
          'Ocurrió un error inesperado. Inténtalo de nuevo.';
        Swal.fire({
          icon: 'error',
          title: mensaje,
          showConfirmButton: false,
          timer: 2500,
        });
      }
    });
  }

  verifyCode() {
    const codeCtrl = this.loginForm.get('verificationCode');
    if (codeCtrl?.invalid) {
      Swal.fire({
        icon: 'error',
        title: 'Ingresa el código de verificación',
        showConfirmButton: false,
        timer: 1800,
      });
      codeCtrl?.markAsTouched();
      return;
    }

    const code = codeCtrl?.value;
    const tempToken = localStorage.getItem(this.tempTokenKey) || '';

    if (!tempToken) {
      Swal.fire({
        icon: 'error',
        title: 'Token temporal no encontrado. Vuelve a iniciar sesión.',
        showConfirmButton: false,
        timer: 2200,
      });
      // Reset: esconder formulario de verificación por seguridad
      this.showVerificationForm = false;
      return;
    }

    this.isVerifying = true;

    this.service.verifyCode({ code }, tempToken).subscribe({
      next: (response: any) => {
        this.isVerifying = false;
        if (response?.message === 'Código verificado correctamente' || /verificad/i.test(response?.message)) {
          // Mover temp token a token oficial (si tu backend maneja tokens finales distintos, ajusta aquí)
          // Si tu backend retorna un token final en esta respuesta, deberías usar ese token en vez de tempToken.
          localStorage.setItem(this.authTokenKey, tempToken);
          localStorage.removeItem(this.tempTokenKey);

          Swal.fire({
            icon: 'success',
            title: 'Código verificado correctamente',
            showConfirmButton: false,
            timer: 1500,
          });

          // Navegar a la app (ajusta la ruta)
          this.router.navigate(['/inventario']);
        } else {
          Swal.fire({
            icon: 'error',
            title: 'Código incorrecto',
            text: response?.message || '',
            showConfirmButton: false,
            timer: 2000,
          });
        }
      },
      error: (error: any) => {
        this.isVerifying = false;
        const mensaje =
          error.error?.error ||
          error.error?.message ||
          error.message ||
          'Hubo un problema al verificar el código';
        Swal.fire({
          icon: 'error',
          title: mensaje,
          showConfirmButton: false,
          timer: 2200,
        });
      }
    });
  }
}
