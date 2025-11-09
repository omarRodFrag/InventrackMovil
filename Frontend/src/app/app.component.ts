import { Component } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  styleUrls: ['app.component.scss'],
  standalone: false,
})
export class AppComponent {
  showNavbar = true;
  hideOnRoutes = ['/login', '/register']; // agrega las rutas donde NO quieres navbar

  constructor(private router: Router) {
    this.router.events.subscribe(ev => {
      if (ev instanceof NavigationEnd) {
        this.showNavbar = !this.hideOnRoutes.includes(ev.urlAfterRedirects);
      }
    });
  }
}
