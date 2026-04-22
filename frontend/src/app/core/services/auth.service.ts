import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly TOKEN_KEY = 'af_token';
  private readonly USER_KEY  = 'af_user';

  currentUser = signal<User | null>(this._loadUser());
  isLoggedIn  = signal<boolean>(!!this._loadToken());

  constructor(private http: HttpClient, private router: Router) {}

  login(email: string, password: string) {
    // OAuth2PasswordRequestForm expects form-encoded body
    const body = new URLSearchParams({ username: email, password });
    return this.http
      .post<AuthResponse>(`${environment.apiUrl}/auth/login`, body.toString(), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      .pipe(tap(res => this._saveSession(res)));
  }

  register(email: string, password: string, full_name: string) {
    return this.http
      .post<User>(`${environment.apiUrl}/auth/register`, { email, password, full_name });
  }

  logout() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.currentUser.set(null);
    this.isLoggedIn.set(false);
    this.router.navigate(['/login']);
  }

  getToken(): string | null {
    return this._loadToken();
  }

  private _saveSession(res: AuthResponse) {
    localStorage.setItem(this.TOKEN_KEY, res.access_token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(res.user));
    this.currentUser.set(res.user);
    this.isLoggedIn.set(true);
  }

  private _loadToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  private _loadUser(): User | null {
    const raw = localStorage.getItem(this.USER_KEY);
    return raw ? JSON.parse(raw) : null;
  }
}
