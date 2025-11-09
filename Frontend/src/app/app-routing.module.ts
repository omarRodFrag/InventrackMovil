import { NgModule } from '@angular/core';
import { PreloadAllModules, RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', loadChildren: () => import('./pages/login/login.module').then(m => m.LoginPageModule) },
  { path: 'inventario', loadChildren: () => import('./pages/inventario/inventario.module').then(m => m.InventarioPageModule) },
  { path: 'agregar-producto', loadChildren: () => import('./pages/agregar-producto/agregar-producto.module').then(m => m.AgregarProductoPageModule) },
  { path: 'cambio-stock', loadChildren: () => import('./pages/cambio-stock/cambio-stock.module').then(m => m.CambioStockPageModule) },
  { path: 'alertas', loadChildren: () => import('./pages/alertas/alertas.module').then(m => m.AlertasPageModule) },
];

@NgModule({
  imports: [
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules })
  ],
  exports: [RouterModule]
})
export class AppRoutingModule { }
