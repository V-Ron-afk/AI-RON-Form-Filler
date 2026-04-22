import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="min-h-[80vh] flex items-center justify-center">
      <div class="w-full max-w-md">

        <!-- Header -->
        <div class="text-center mb-8">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center mx-auto mb-4 shadow-xl shadow-violet-500/30">
            <svg class="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-white">Welcome back</h1>
          <p class="text-slate-400 mt-1 text-sm">Sign in to your AI Form Filler account</p>
        </div>

        <!-- Card -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">

          <div *ngIf="error" class="mb-5 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            {{ error }}
          </div>

          <form (ngSubmit)="submit()" #f="ngForm" class="space-y-5">

            <div>
              <label class="block text-sm font-medium text-slate-300 mb-1.5">Email</label>
              <input type="email" name="email" [(ngModel)]="email" required
                class="w-full px-4 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-500
                       focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors text-sm"
                placeholder="you@example.com">
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
              <input type="password" name="password" [(ngModel)]="password" required
                class="w-full px-4 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-500
                       focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors text-sm"
                placeholder="••••••••">
            </div>

            <button type="submit" [disabled]="loading || !f.valid"
              class="w-full py-2.5 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:text-slate-500
                     text-white font-medium transition-colors text-sm flex items-center justify-center gap-2">
              <svg *ngIf="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
              </svg>
              {{ loading ? 'Signing in…' : 'Sign in' }}
            </button>
          </form>

          <p class="text-center text-sm text-slate-500 mt-6">
            Don't have an account?
            <a routerLink="/register" class="text-violet-400 hover:text-violet-300 ml-1">Create one</a>
          </p>

        </div>
      </div>
    </div>
  `
})
export class LoginComponent {
  private auth   = inject(AuthService);
  private router = inject(Router);

  email    = '';
  password = '';
  loading  = false;
  error    = '';

  submit() {
    this.loading = true;
    this.error   = '';
    this.auth.login(this.email, this.password).subscribe({
      next: () => this.router.navigate(['/upload']),
      error: err => {
        this.error   = err.error?.detail || 'Login failed. Please try again.';
        this.loading = false;
      }
    });
  }
}
