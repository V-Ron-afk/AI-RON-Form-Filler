import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="min-h-[80vh] flex items-center justify-center">
      <div class="w-full max-w-md">

        <div class="text-center mb-8">
          <h1 class="text-2xl font-bold text-white">Create your account</h1>
          <p class="text-slate-400 mt-1 text-sm">Start auto-filling forms with AI</p>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">

          <div *ngIf="error" class="mb-5 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            {{ error }}
          </div>
          <div *ngIf="success" class="mb-5 px-4 py-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm">
            Account created! Redirecting to login…
          </div>

          <form (ngSubmit)="submit()" #f="ngForm" class="space-y-5">

            <div>
              <label class="block text-sm font-medium text-slate-300 mb-1.5">Full Name</label>
              <input type="text" name="full_name" [(ngModel)]="fullName" required
                class="w-full px-4 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-500
                       focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors text-sm"
                placeholder="Maria Santos">
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-300 mb-1.5">Email</label>
              <input type="email" name="email" [(ngModel)]="email" required
                class="w-full px-4 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-500
                       focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors text-sm"
                placeholder="you@example.com">
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
              <input type="password" name="password" [(ngModel)]="password" required minlength="8"
                class="w-full px-4 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-500
                       focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors text-sm"
                placeholder="Min. 8 characters">
            </div>

            <button type="submit" [disabled]="loading || !f.valid"
              class="w-full py-2.5 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:text-slate-500
                     text-white font-medium transition-colors text-sm flex items-center justify-center gap-2">
              <svg *ngIf="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
              </svg>
              {{ loading ? 'Creating account…' : 'Create account' }}
            </button>
          </form>

          <p class="text-center text-sm text-slate-500 mt-6">
            Already have an account?
            <a routerLink="/login" class="text-violet-400 hover:text-violet-300 ml-1">Sign in</a>
          </p>

        </div>
      </div>
    </div>
  `
})
export class RegisterComponent {
  private auth   = inject(AuthService);
  private router = inject(Router);

  fullName = '';
  email    = '';
  password = '';
  loading  = false;
  error    = '';
  success  = false;

  submit() {
    this.loading = true;
    this.error   = '';
    this.auth.register(this.email, this.password, this.fullName).subscribe({
      next: () => {
        this.success = true;
        setTimeout(() => this.router.navigate(['/login']), 1500);
      },
      error: err => {
        this.error   = err.error?.detail || 'Registration failed.';
        this.loading = false;
      }
    });
  }
}
