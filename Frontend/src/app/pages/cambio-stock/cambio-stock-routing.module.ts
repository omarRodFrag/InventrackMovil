import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { CambioStockPage } from './cambio-stock.page';

const routes: Routes = [
  {
    path: '',
    component: CambioStockPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class CambioStockPageRoutingModule {}
