import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface DocumentRecord {
  id: number;
  filename: string;
  file_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  extracted_data: any | null;
  created_at: string;
  processed_at: string | null;
}

export interface ExtractedField {
  key: string;
  value: string | null;
  confidence: number;
  page: number | null;
}

export interface ExtractionResponse {
  document_id: number;
  status: string;
  model_used: string;
  raw_text_preview: string;
  fields: ExtractedField[];
  tables: any[][];
  form_values: Record<string, string | null>;
  confidence_map: Record<string, number>;
  form_schema: FormFieldDef[];
}

export interface FormFieldDef {
  name: string;
  label: string;
  field_type: 'text' | 'date' | 'number' | 'email' | 'select';
  required: boolean;
  options?: string[];
}

export interface FormSubmission {
  id: number;
  document_id: number;
  form_data: Record<string, any>;
  label: string | null;
  created_at: string;
}

@Injectable({ providedIn: 'root' })
export class DocumentService {
  private base = environment.apiUrl;

  constructor(private http: HttpClient) {}

  uploadDocument(file: File): Observable<DocumentRecord> {
    const fd = new FormData();
    fd.append('file', file);
    return this.http.post<DocumentRecord>(`${this.base}/documents/upload`, fd);
  }

  getExtractionResult(docId: number): Observable<ExtractionResponse> {
    return this.http.get<ExtractionResponse>(`${this.base}/documents/${docId}/extraction`);
  }

  listDocuments(): Observable<DocumentRecord[]> {
    return this.http.get<DocumentRecord[]>(`${this.base}/documents/`);
  }

  submitForm(documentId: number, formData: Record<string, any>, label?: string): Observable<FormSubmission> {
    return this.http.post<FormSubmission>(`${this.base}/forms/submit`, {
      document_id: documentId,
      form_data: formData,
      label
    });
  }

  listSubmissions(): Observable<FormSubmission[]> {
    return this.http.get<FormSubmission[]>(`${this.base}/forms/`);
  }

  downloadJson(submissionId: number): Observable<Blob> {
    return this.http.get(`${this.base}/export/${submissionId}/json`, { responseType: 'blob' });
  }

  downloadPdf(submissionId: number): Observable<Blob> {
    return this.http.get(`${this.base}/export/${submissionId}/pdf`, { responseType: 'blob' });
  }
}
