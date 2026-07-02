import { useState, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table';
import { Upload, FileText, Loader2 } from 'lucide-react';
import api from '@/lib/api';

interface DocumentItem {
  id: string;
  filename: string;
  mime_type: string;
  file_size_bytes: number;
  doc_type: string;
  ocr_status: string;
  created_at: string;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setIsUploading(true);
      const res = await api.post<DocumentItem>('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setDocuments((prev) => [res.data, ...prev]);
    } catch (error) {
      console.error('Failed to upload document:', error);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Documents</h1>
          <p className="text-muted-foreground">Upload and manage appraisal documents.</p>
        </div>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          accept=".pdf,.png,.jpg,.jpeg"
        />
        <Button onClick={handleUploadClick} disabled={isUploading}>
          {isUploading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Upload className="mr-2 h-4 w-4" />
          )}
          {isUploading ? 'Uploading...' : 'Upload Document'}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Documents</CardTitle>
          <CardDescription>Uploaded documents with OCR status.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {documents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4}>
                    <div className="flex flex-col items-center justify-center py-8 text-center">
                      <FileText className="h-12 w-12 text-muted-foreground/30" />
                      <p className="mt-4 text-muted-foreground">
                        No documents uploaded yet. Upload appraisal documents to begin OCR processing.
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                documents.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell className="font-medium">{doc.filename}</TableCell>
                    <TableCell>{doc.mime_type || 'Unknown'}</TableCell>
                    <TableCell>
                      {doc.file_size_bytes
                        ? `${(doc.file_size_bytes / 1024).toFixed(1)} KB`
                        : 'N/A'}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          doc.ocr_status === 'completed'
                            ? 'success'
                            : doc.ocr_status === 'processing'
                            ? 'warning'
                            : 'secondary'
                        }
                      >
                        {doc.ocr_status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}