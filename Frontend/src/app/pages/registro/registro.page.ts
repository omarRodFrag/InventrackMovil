import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { ToastController } from '@ionic/angular';
import { Login } from 'src/app/interface/login.interface';
import { ServiceService } from 'src/app/services/service';

@Component({
  selector: 'app-registro',
  templateUrl: './registro.page.html',
  styleUrls: ['./registro.page.scss'],
  standalone: false
})
export class RegistroPage implements OnInit {
  registroForm!: FormGroup;
  isLoading: boolean = false;

  constructor(
    private fb: FormBuilder,
    private service: ServiceService,
    private router: Router,
    private toastCtrl: ToastController
  ) {}

  ngOnInit(): void {
    this.registroForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', [Validators.required]]
    }, { validators: this.passwordMatchValidator });
  }

  // Validador personalizado para verificar que las contraseñas coincidan
  passwordMatchValidator(form: FormGroup) {
    const password = form.get('password');
    const confirmPassword = form.get('confirmPassword');
    
    if (password && confirmPassword) {
      if (password.value !== confirmPassword.value) {
        confirmPassword.setErrors({ passwordMismatch: true });
        return { passwordMismatch: true };
      } else {
        // Limpiar errores si coinciden
        if (confirmPassword.hasError('passwordMismatch')) {
          confirmPassword.setErrors(null);
        }
      }
    }
    return null;
  }

  // Helper: toast rápido
  private async presentToast(message: string, color: 'success' | 'danger' | 'warning' | 'primary' = 'danger', duration = 2000) {
    const toast = await this.toastCtrl.create({
      message,
      duration,
      color,
      position: 'top'
    });
    await toast.present();
  }

  register() {
    if (this.registroForm.invalid) {
      this.presentToast('Revisa los campos del formulario.', 'danger', 2200);
      return;
    }

    // Verificar que las contraseñas coincidan
    if (this.registroForm.get('password')?.value !== this.registroForm.get('confirmPassword')?.value) {
      this.presentToast('Las contraseñas no coinciden.', 'danger', 2200);
      return;
    }

    this.isLoading = true;

    const registroData: Login = {
      strEmail: this.registroForm.value.email,
      strPassword: this.registroForm.value.password,
    };

    this.service.register(registroData).subscribe({
      next: async (response: any) => {
        this.isLoading = false;
        if (response?.message && response?.intResponse === 201) {
          await this.presentToast('Usuario registrado correctamente', 'success', 2000);
          // Redirigir a login después de 1 segundo
          setTimeout(() => {
            this.router.navigate(['/login']);
          }, 1000);
        } else {
          const errorMsg = response?.error || response?.message || 'Error al registrar usuario';
          await this.presentToast(errorMsg, 'danger', 2500);
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
}

