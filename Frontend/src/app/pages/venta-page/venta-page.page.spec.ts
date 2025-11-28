import { ComponentFixture, TestBed } from '@angular/core/testing';
import { VentaPagePage } from './venta-page.page';

describe('VentaPagePage', () => {
  let component: VentaPagePage;
  let fixture: ComponentFixture<VentaPagePage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(VentaPagePage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
