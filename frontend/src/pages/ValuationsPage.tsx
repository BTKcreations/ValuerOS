import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table';
import { Plus, FileSpreadsheet } from 'lucide-react';

export default function ValuationsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Valuations</h1>
          <p className="text-muted-foreground">Track and manage property valuations.</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Valuation
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Valuations</CardTitle>
          <CardDescription>Recent valuation reports and drafts.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Property</TableHead>
                <TableHead>Methodology</TableHead>
                <TableHead>Estimated Value</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell colSpan={4}>
                  <div className="flex flex-col items-center justify-center py-8 text-center">
                    <FileSpreadsheet className="h-12 w-12 text-muted-foreground/30" />
                    <p className="mt-4 text-muted-foreground">
                      No valuations yet. Create your first valuation to begin.
                    </p>
                  </div>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}