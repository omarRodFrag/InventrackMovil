export interface Producto {
  _id?: string;              // ID asignado por MongoDB
  idProducto:number
  nombre: string;            // Nombre del producto
  descripcion: string;       // Descripción breve
  categoria: string;         // Ej: "Alimentos", "Limpieza", etc.
  cantidad: number;          // Stock actual
  stockMinimo: number;       // Umbral para generar alerta
  activo: boolean;           // Si está disponible o no
}