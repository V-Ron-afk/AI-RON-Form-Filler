import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { DocumentService, ExtractionResponse, FormFieldDef } from '../../core/services/document.service';

@Component({
  selector: 'app-form',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="max-w-3xl mx-auto">

      <!-- Loading state -->
      <div *ngIf="loading" class="flex flex-col items-center justify-center py-24 gap-4">
        <div class="w-12 h-12 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"></div>
        <p class="text-slate-400">Loading extraction results…</p>
      </div>

      <!-- Error state -->
      <div *ngIf="error && !loading" class="p-6 bg-red-500/10 border border-red-500/30 rounded-2xl text-red-400">
        <p class="font-medium">⚠️ {{ error }}</p>
        <button (click)="goBack()" class="mt-3 text-sm underline text-red-400/70">Go back</button>
      </div>

      <!-- Form view -->
      <div *ngIf="!loading && extraction">

        <!-- Header -->
        <div class="flex items-start justify-between mb-6 gap-4">
          <div>
            <h1 class="text-2xl font-bold text-white">Review & Edit</h1>
            <p class="text-slate-400 mt-1 text-sm">
              AI extracted {{ filledCount }} of {{ totalCount }} fields.
              Edit any values before saving.
            </p>
          </div>
          <div class="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-400">
            <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
            {{ extraction.model_used }}
          </div>
        </div>

        <!-- Confidence legend -->
        <div class="flex items-center gap-4 mb-6 p-3 bg-slate-900/50 border border-slate-800 rounded-xl text-xs">
          <span class="text-slate-500 font-medium">Confidence:</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-emerald-400"></span>High (≥90%)</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-amber-400"></span>Medium (70–89%)</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-red-400"></span>Low (&lt;70%)</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-slate-600"></span>Not found</span>
        </div>

        <!-- Dynamic form fields -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <div class="divide-y divide-slate-800">
            <div *ngFor="let field of extraction.form_schema" class="p-5">

              <div class="flex items-center justify-between mb-2">
                <label class="text-sm font-medium text-slate-300 flex items-center gap-2">
                  {{ field.label }}
                  <span *ngIf="field.required"
                    class="text-xs text-violet-400 font-normal">required</span>
                </label>

                <!-- Confidence badge -->
                <div class="flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full"
                    [class]="getConfidenceColor(field.name)"></span>
                  <span class="text-xs text-slate-500">
                    {{ getConfidenceLabel(field.name) }}
                  </span>
                </div>
              </div>

              <!-- Text / Email / Number input -->
              <input *ngIf="['text','email','number'].includes(field.field_type)"
                [type]="field.field_type"
                [(ngModel)]="formValues[field.name]"
                [name]="field.name"
                [placeholder]="'Enter ' + field.label"
                class="w-full px-4 py-2.5 rounded-lg text-sm transition-colors
                       focus:outline-none focus:ring-1 text-white placeholder-slate-600"
                [class]="getInputClass(field.name)">

              <!-- Date input -->
              <input *ngIf="field.field_type === 'date'"
                type="date"
                [(ngModel)]="formValues[field.name]"
                [name]="field.name"
                class="w-full px-4 py-2.5 rounded-lg text-sm transition-colors
                       focus:outline-none focus:ring-1 text-white"
                [class]="getInputClass(field.name)">

              <!-- Select input -->
              <select *ngIf="field.field_type === 'select'"
                [(ngModel)]="formValues[field.name]"
                [name]="field.name"
                class="w-full px-4 py-2.5 rounded-lg text-sm transition-colors
                       focus:outline-none focus:ring-1 text-white bg-slate-800"
                [class]="getInputClass(field.name)">
                <option value="">-- Select --</option>
                <option *ngFor="let opt of field.options" [value]="opt">{{ opt }}</option>
              </select>

            </div>
          </div>
        </div>

        <!-- Tables section -->
        <div *ngIf="extraction.tables.length" class="mt-6">
          <h3 class="text-sm font-semibold text-slate-300 mb-3">Extracted Tables</h3>
          <div *ngFor="let table of extraction.tables; let ti = index"
               class="bg-slate-900 border border-slate-800 rounded-xl overflow-x-auto mb-4">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-slate-800">
                  <th *ngFor="let col of getTableColumns(table)"
                    class="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                    {{ col }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr *ngFor="let row of table" class="border-b border-slate-800/50 last:border-0">
                  <td *ngFor="let col of getTableColumns(table)"
                    class="px-4 py-3 text-slate-300">
                    {{ row[col] || '—' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Success alert -->
        <div *ngIf="saveSuccess"
          class="mt-4 px-4 py-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
          </svg>
          Form saved! Submission ID: #{{ submissionId }}
        </div>

        <!-- Action buttons -->
        <div class="flex flex-wrap items-center gap-3 mt-6">

          <button (click)="save()" [disabled]="saving"
            class="flex-1 sm:flex-none px-6 py-2.5 bg-violet-600 hover:bg-violet-500
                   disabled:bg-slate-700 disabled:text-slate-500
                   text-white font-medium rounded-lg transition-colors text-sm flex items-center justify-center gap-2">
            <svg *ngIf="saving" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
            </svg>
            {{ saving ? 'Saving…' : '💾 Save Submission' }}
          </button>

          <button *ngIf="submissionId" (click)="downloadJson()"
            class="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium rounded-lg transition-colors text-sm border border-slate-700">
            ⬇ JSON
          </button>

          <button *ngIf="submissionId" (click)="downloadPdf()"
            class="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium rounded-lg transition-colors text-sm border border-slate-700">
            ⬇ PDF
          </button>

          <button (click)="goBack()"
            class="px-5 py-2.5 text-slate-400 hover:text-slate-300 font-medium rounded-lg transition-colors text-sm">
            ← Upload another
          </button>

        </div>

      </div>
    </div>
  `
})
export class FormComponent implements OnInit {
  private route  = inject(ActivatedRoute);
  private router = inject(Router);
  private docSvc = inject(DocumentService);

  extraction: ExtractionResponse | null = null;
  formValues: Record<string, any> = {};
  loading     = true;
  saving      = false;
  error       = '';
  saveSuccess = false;
  submissionId: number | null = null;
  docId = 0;

  get filledCount() {
    return Object.values(this.formValues).filter(v => v != null && v !== '').length;
  }
  get totalCount() {
    return this.extraction?.form_schema?.length ?? 0;
  }

  ngOnInit() {
    this.docId = Number(this.route.snapshot.paramMap.get('docId'));
    this.docSvc.getExtractionResult(this.docId).subscribe({
      next: res => {
        this.extraction = res;
        this.formValues = { ...res.form_values };
        this.loading = false;
      },
      error: err => {
        this.error   = err.error?.detail || 'Could not load extraction results.';
        this.loading = false;
      }
    });
  }

  getConfidence(fieldName: string): number | null {
    return this.extraction?.confidence_map?.[fieldName] ?? null;
  }

  getConfidenceColor(fieldName: string): string {
    const c = this.getConfidence(fieldName);
    if (c === null) return 'bg-slate-600';
    if (c >= 0.9)   return 'bg-emerald-400';
    if (c >= 0.7)   return 'bg-amber-400';
    return 'bg-red-400';
  }

  getConfidenceLabel(fieldName: string): string {
    const c = this.getConfidence(fieldName);
    if (c === null) return 'Not found';
    return `${Math.round(c * 100)}%`;
  }

  getInputClass(fieldName: string): string {
    const c = this.getConfidence(fieldName);
    const base = 'bg-slate-800 border ';
    if (c === null)  return base + 'border-slate-700 focus:border-slate-500 focus:ring-slate-500';
    if (c >= 0.9)    return base + 'border-emerald-500/40 focus:border-emerald-500 focus:ring-emerald-500';
    if (c >= 0.7)    return base + 'border-amber-500/40 focus:border-amber-500 focus:ring-amber-500';
    return base + 'border-red-500/40 focus:border-red-500 focus:ring-red-500';
  }

  getTableColumns(table: any[]): string[] {
    if (!table.length) return [];
    return Object.keys(table[0]);
  }

  save() {
    this.saving = true;
    this.docSvc.submitForm(this.docId, this.formValues).subscribe({
      next: sub => {
        this.submissionId = sub.id;
        this.saveSuccess  = true;
        this.saving       = false;
      },
      error: err => {
        this.error  = err.error?.detail || 'Save failed.';
        this.saving = false;
      }
    });
  }

  downloadJson() {
    if (!this.submissionId) return;
    this.docSvc.downloadJson(this.submissionId).subscribe(blob => {
      this._triggerDownload(blob, `submission_${this.submissionId}.json`);
    });
  }

  downloadPdf() {
    if (!this.submissionId) return;
    this.docSvc.downloadPdf(this.submissionId).subscribe(blob => {
      this._triggerDownload(blob, `submission_${this.submissionId}.pdf`);
    });
  }

  private _triggerDownload(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const a   = document.createElement('a');
    a.href    = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  goBack() {
    this.router.navigate(['/upload']);
  }
}
