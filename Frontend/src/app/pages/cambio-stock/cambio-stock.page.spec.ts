import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CambioStockPage } from './cambio-stock.page';

describe('CambioStockPage', () => {
  let component: CambioStockPage;
  let fixture: ComponentFixture<CambioStockPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(CambioStockPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
