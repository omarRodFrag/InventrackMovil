import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { CambioStockPageRoutingModule } from './cambio-stock-routing.module';

import { CambioStockPage } from './cambio-stock.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    CambioStockPageRoutingModule
  ],
  declarations: [CambioStockPage]
})
export class CambioStockPageModule {}
