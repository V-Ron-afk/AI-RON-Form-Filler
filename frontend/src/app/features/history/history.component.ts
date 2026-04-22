import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { DocumentService, DocumentRecord, FormSubmission } from '../../core/services/document.service';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="max-w-4xl mx-auto">

      <div class="mb-8">
        <h1 class="text-2xl font-bold text-white">History</h1>
        <p class="text-slate-400 mt-1">All your uploaded documents and saved submissions.</p>
      </div>

      <!-- Tabs -->
      <div class="flex gap-1 mb-6 bg-slate-900 border border-slate-800 rounded-xl p-1 w-fit">
        <button *ngFor="let tab of tabs"
          (click)="activeTab = tab.id"
          class="px-4 py-1.5 rounded-lg text-sm font-medium transition-colors"
          [class]="activeTab === tab.id
            ? 'bg-violet-600 text-white'
            : 'text-slate-400 hover:text-white'">
          {{ tab.label }}
        </button>
      </div>

      <!-- Documents tab -->
      <div *ngIf="activeTab === 'docs'">
        <div *ngIf="docsLoading" class="text-slate-500 text-sm py-8 text-center">Loading…</div>

        <div *ngIf="!docsLoading && documents.length === 0"
          class="text-center py-16 text-slate-500">
          <p class="text-4xl mb-3">📂</p>
          <p>No documents uploaded yet.</p>
        </div>

        <div class="space-y-3">
          <div *ngFor="let doc of documents"
            class="flex items-center gap-4 p-4 bg-slate-900 border border-slate-800 rounded-xl
                   hover:border-slate-700 transition-colors cursor-pointer"
            (click)="openDoc(doc)">

            <!-- File icon -->
            <div class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                 [class]="getFileIconClass(doc.file_type)">
              <span class="text-lg">{{ getFileIcon(doc.file_type) }}</span>
            </div>

            <!-- Info -->
            <div class="flex-1 min-w-0">
              <p class="text-sm text-white font-medium truncate">{{ doc.filename }}</p>
              <p class="text-xs text-slate-500 mt-0.5">{{ doc.created_at | date:'MMM d, y · h:mm a' }}</p>
            </div>

            <!-- Status badge -->
            <span class="px-2.5 py-1 rounded-md text-xs font-medium flex-shrink-0"
              [class]="getStatusClass(doc.status)">
              {{ doc.status }}
            </span>

            <!-- Arrow -->
            <svg class="w-4 h-4 text-slate-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </div>
        </div>
      </div>

      <!-- Submissions tab -->
      <div *ngIf="activeTab === 'subs'">
        <div *ngIf="subsLoading" class="text-slate-500 text-sm py-8 text-center">Loading…</div>

        <div *ngIf="!subsLoading && submissions.length === 0"
          class="text-center py-16 text-slate-500">
          <p class="text-4xl mb-3">📋</p>
          <p>No submissions saved yet.</p>
        </div>

        <div class="space-y-3">
          <div *ngFor="let sub of submissions"
            class="p-4 bg-slate-900 border border-slate-800 rounded-xl">

            <div class="flex items-center justify-between mb-3">
              <div>
                <p class="text-sm font-medium text-white">Submission #{{ sub.id }}</p>
                <p class="text-xs text-slate-500">{{ sub.created_at | date:'MMM d, y · h:mm a' }}</p>
              </div>
              <div class="flex gap-2">
                <button (click)="downloadJson(sub.id)"
                  class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg border border-slate-700 transition-colors">
                  JSON
                </button>
                <button (click)="downloadPdf(sub.id)"
                  class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg border border-slate-700 transition-colors">
                  PDF
                </button>
              </div>
            </div>

            <!-- Preview fields -->
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <div *ngFor="let kv of getPreviewFields(sub.form_data)"
                class="bg-slate-800/50 rounded-lg px-3 py-2">
                <p class="text-xs text-slate-500 capitalize">{{ kv.key.replace('_', ' ') }}</p>
                <p class="text-xs text-slate-300 font-medium truncate mt-0.5">{{ kv.value || '—' }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  `
})
export class HistoryComponent implements OnInit {
  private docSvc = inject(DocumentService);
  private router = inject(Router);

  activeTab   = 'docs';
  tabs        = [{ id: 'docs', label: 'Documents' }, { id: 'subs', label: 'Submissions' }];

  documents:   DocumentRecord[]  = [];
  submissions: FormSubmission[]  = [];
  docsLoading = true;
  subsLoading = true;

  ngOnInit() {
    this.docSvc.listDocuments().subscribe({
      next: docs => { this.documents = docs; this.docsLoading = false; },
      error: ()  => { this.docsLoading = false; }
    });
    this.docSvc.listSubmissions().subscribe({
      next: subs => { this.submissions = subs; this.subsLoading = false; },
      error: ()  => { this.subsLoading = false; }
    });
  }

  openDoc(doc: DocumentRecord) {
    if (doc.status === 'completed') {
      this.router.navigate(['/form', doc.id]);
    }
  }

  getFileIcon(type: string) {
    return type === 'pdf' ? '📄' : '🖼️';
  }

  getFileIconClass(type: string) {
    return type === 'pdf'
      ? 'bg-red-500/10 border border-red-500/20'
      : 'bg-blue-500/10 border border-blue-500/20';
  }

  getStatusClass(status: string) {
    const map: Record<string, string> = {
      completed:  'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
      processing: 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
      pending:    'bg-slate-700 text-slate-400',
      failed:     'bg-red-500/10 text-red-400 border border-red-500/20',
    };
    return map[status] || map['pending'];
  }

  getPreviewFields(data: Record<string, any>) {
    const priority = ['full_name', 'email', 'date_of_birth', 'id_number', 'phone'];
    return priority
      .filter(k => k in data)
      .slice(0, 6)
      .map(k => ({ key: k, value: data[k] }));
  }

  downloadJson(subId: number) {
    this.docSvc.downloadJson(subId).subscribe(blob =>
      this._save(blob, `submission_${subId}.json`)
    );
  }

  downloadPdf(subId: number) {
    this.docSvc.downloadPdf(subId).subscribe(blob =>
      this._save(blob, `submission_${subId}.pdf`)
    );
  }

  private _save(blob: Blob, name: string) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = name; a.click();
    URL.revokeObjectURL(url);
  }
}
