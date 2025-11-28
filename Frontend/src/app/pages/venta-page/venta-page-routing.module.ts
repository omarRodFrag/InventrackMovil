import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { VentaPagePage } from './venta-page.page';

const routes: Routes = [
  {
    path: '',
    component: VentaPagePage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class VentaPagePageRoutingModule {}
