import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { DocumentService } from '../../core/services/document.service';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="max-w-2xl mx-auto">

      <!-- Page header -->
      <div class="mb-8">
        <h1 class="text-2xl font-bold text-white">Upload Document</h1>
        <p class="text-slate-400 mt-1">Upload a PDF or image — AI will extract all form fields automatically.</p>
      </div>

      <!-- Drop zone -->
      <div
        class="relative border-2 border-dashed rounded-2xl transition-all duration-200 cursor-pointer"
        [class]="isDragging
          ? 'border-violet-500 bg-violet-500/5'
          : 'border-slate-700 bg-slate-900 hover:border-slate-600'"
        (dragover)="onDragOver($event)"
        (dragleave)="onDragLeave()"
        (drop)="onDrop($event)"
        (click)="fileInput.click()">

        <input #fileInput type="file" class="hidden"
          accept=".pdf,.jpg,.jpeg,.png,.tiff,.bmp"
          (change)="onFileSelected($event)">

        <div class="flex flex-col items-center justify-center py-16 px-8 text-center">

          <!-- Icon -->
          <div class="w-16 h-16 rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center mb-5"
               [class.border-violet-500]="isDragging">
            <svg class="w-8 h-8 text-slate-400" [class.text-violet-400]="isDragging"
                 fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/>
            </svg>
          </div>

          <p class="text-white font-medium mb-1">
            {{ isDragging ? 'Drop it here!' : 'Drag & drop your document' }}
          </p>
          <p class="text-slate-500 text-sm mb-4">or click to browse</p>
          <p class="text-slate-600 text-xs">PDF, JPG, PNG, TIFF — up to 20 MB</p>
        </div>
      </div>

      <!-- Selected file info -->
      <div *ngIf="selectedFile && !loading" class="mt-4 flex items-center gap-3 p-4 bg-slate-900 border border-slate-800 rounded-xl">
        <div class="w-10 h-10 rounded-lg bg-violet-500/10 border border-violet-500/30 flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm text-white font-medium truncate">{{ selectedFile.name }}</p>
          <p class="text-xs text-slate-500">{{ formatSize(selectedFile.size) }}</p>
        </div>
        <button (click)="upload()"
          class="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors">
          Process with AI
        </button>
      </div>

      <!-- Upload progress -->
      <div *ngIf="loading" class="mt-6 p-6 bg-slate-900 border border-slate-800 rounded-2xl">
        <div class="flex items-center gap-4 mb-4">
          <div class="w-10 h-10 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"></div>
          <div>
            <p class="text-white font-medium">{{ statusMessage }}</p>
            <p class="text-slate-500 text-sm">This may take a few seconds…</p>
          </div>
        </div>
        <!-- Animated progress bar -->
        <div class="h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div class="h-full bg-gradient-to-r from-violet-600 to-cyan-500 rounded-full animate-pulse"
               style="width: 60%"></div>
        </div>
      </div>

      <!-- Error -->
      <div *ngIf="error" class="mt-4 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
        ⚠️ {{ error }}
      </div>

      <!-- Supported formats -->
      <div class="mt-8 grid grid-cols-3 gap-3">
        <div *ngFor="let fmt of formats"
          class="flex items-center gap-2.5 p-3 bg-slate-900/50 border border-slate-800 rounded-xl">
          <span class="text-xl">{{ fmt.icon }}</span>
          <div>
            <p class="text-white text-xs font-medium">{{ fmt.label }}</p>
            <p class="text-slate-500 text-xs">{{ fmt.desc }}</p>
          </div>
        </div>
      </div>

    </div>
  `
})
export class UploadComponent {
  private docSvc = inject(DocumentService);
  private router = inject(Router);

  isDragging    = false;
  selectedFile: File | null = null;
  loading       = false;
  error         = '';
  statusMessage = 'Uploading document…';

  formats = [
    { icon: '📄', label: 'PDF', desc: 'Forms, invoices' },
    { icon: '🖼️', label: 'JPG / PNG', desc: 'Scanned images' },
    { icon: '📑', label: 'TIFF / BMP', desc: 'High-res scans' },
  ];

  onDragOver(e: DragEvent) {
    e.preventDefault();
    this.isDragging = true;
  }

  onDragLeave() {
    this.isDragging = false;
  }

  onDrop(e: DragEvent) {
    e.preventDefault();
    this.isDragging = false;
    const file = e.dataTransfer?.files?.[0];
    if (file) this.selectFile(file);
  }

  onFileSelected(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) this.selectFile(file);
  }

  selectFile(file: File) {
    this.error = '';
    this.selectedFile = file;
  }

  upload() {
    if (!this.selectedFile) return;
    this.loading = true;
    this.error   = '';
    this.statusMessage = 'Uploading document…';

    this.docSvc.uploadDocument(this.selectedFile).subscribe({
      next: doc => {
        this.statusMessage = 'Running AI extraction…';
        // Small delay for UX — the extraction happens server-side during upload
        setTimeout(() => this.router.navigate(['/form', doc.id]), 800);
      },
      error: err => {
        this.error   = err.error?.detail || 'Upload failed. Please try again.';
        this.loading = false;
      }
    });
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
}
