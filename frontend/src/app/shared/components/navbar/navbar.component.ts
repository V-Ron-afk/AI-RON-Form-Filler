import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, CommonModule],
  template: `
    <nav class="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">

          <!-- Logo -->
          <a routerLink="/" class="flex items-center gap-2.5 group">
            <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-violet-500/30">
              <svg class="w-4.5 h-4.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <span class="font-bold text-white tracking-tight">AI Form<span class="text-violet-400">Filler</span></span>
          </a>

          <!-- Nav links (authenticated) -->
          <div *ngIf="auth.isLoggedIn()" class="flex items-center gap-1">
            <a routerLink="/upload" routerLinkActive="bg-slate-800 text-white"
               class="px-3 py-1.5 rounded-md text-sm text-slate-400 hover:text-white hover:bg-slate-800 transition-colors">
              Upload
            </a>
            <a routerLink="/history" routerLinkActive="bg-slate-800 text-white"
               class="px-3 py-1.5 rounded-md text-sm text-slate-400 hover:text-white hover:bg-slate-800 transition-colors">
              History
            </a>
          </div>

          <!-- Right actions -->
          <div class="flex items-center gap-3">
            <ng-container *ngIf="auth.isLoggedIn(); else guestActions">
              <span class="text-sm text-slate-400 hidden sm:block">{{ auth.currentUser()?.full_name }}</span>
              <button (click)="auth.logout()"
                class="px-3 py-1.5 rounded-md text-sm text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 transition-colors">
                Sign out
              </button>
            </ng-container>
            <ng-template #guestActions>
              <a routerLink="/login"
                class="px-3 py-1.5 rounded-md text-sm text-slate-400 hover:text-white transition-colors">
                Sign in
              </a>
              <a routerLink="/register"
                class="px-3 py-1.5 rounded-md text-sm bg-violet-600 hover:bg-violet-500 text-white transition-colors">
                Get started
              </a>
            </ng-template>
          </div>

        </div>
      </div>
    </nav>
  `
})
export class NavbarComponent {
  auth = inject(AuthService);
}
