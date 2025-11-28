import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { VentaPagePageRoutingModule } from './venta-page-routing.module';

import { VentaPagePage } from './venta-page.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    VentaPagePageRoutingModule,
    ReactiveFormsModule
  ],
  declarations: [VentaPagePage]
})
export class VentaPagePageModule {}
