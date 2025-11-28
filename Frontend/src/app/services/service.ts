import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Login } from '../interface/login.interface';
import { Producto } from '../interface/producto.interface';

interface LoginResponse {
  message: string;
  token: string;
}

interface VerifyCodeResponse {
  message: string;
}

@Injectable({
  providedIn: 'root',
})
export class ServiceService {
  private baseUrl = 'http://localhost:5000'; // URL de tu backend

  constructor(private http: HttpClient) { }

  // --- Headers con token ---
  private getAuthHeaders(token: string): HttpHeaders {
    return new HttpHeaders().set('Authorization', `Bearer ${token}`);
  }

  // --- Login con JWT ---
  login(data: Login): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.baseUrl}/login`, data);
  }

  // --- Verificar código ---
  verifyCode(body: { code: string }, token: string): Observable<VerifyCodeResponse> {
    return this.http.post<VerifyCodeResponse>(
      `${this.baseUrl}/verify`,
      body,
      { headers: this.getAuthHeaders(token) }
    );
  }

  // --- Productos ---
  obtenerProductoPorId(id: string, token: string): Observable<Producto> {
    return this.http.get<Producto>(`${this.baseUrl}/productos/${id}`, {
      headers: this.getAuthHeaders(token),
    });
  }

  obtenerProductos(token: string): Observable<Producto[]> {
    return this.http.get<Producto[]>(`${this.baseUrl}/productos`, {
      headers: this.getAuthHeaders(token),
    });
  }

  agregarProducto(producto: Producto, token: string): Observable<Producto> {
    return this.http.post<Producto>(`${this.baseUrl}/productos/agregar`, producto, {
      headers: this.getAuthHeaders(token),
    });
  }

  actualizarProducto(id: string, producto: Producto, token: string): Observable<Producto> {
    return this.http.put<Producto>(`${this.baseUrl}/productos/actualizar/${id}`, producto, {
      headers: this.getAuthHeaders(token),
    });
  }

  eliminarProducto(id: number, token: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/productos/eliminar/${id}`, {
      headers: this.getAuthHeaders(token),
    });
  }

  actualizarEstadoProducto(id: number, activo: boolean, token: string): Observable<any> {
    return this.http.patch(
      `${this.baseUrl}/productos/estado/${id}`,
      { activo },
      { headers: this.getAuthHeaders(token) }
    );
  }

  // --- Venta (Punto de Venta) ---
  ventaPorNombre(body: { nombre: string; cantidad: number }, token: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/venta`, body, {
      headers: this.getAuthHeaders(token)
    });
  }
}
