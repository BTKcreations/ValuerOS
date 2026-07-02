import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/hooks/useAuth';
import {
  Building2,
  FileSpreadsheet,
  FileText,
  FileBarChart,
  TrendingUp,
  Clock,
} from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuth();

  const stats = [
    { label: 'Properties', value: '—', icon: Building2, color: 'default' as const },
    { label: 'Active Valuations', value: '—', icon: FileSpreadsheet, color: 'success' as const },
    { label: 'Documents', value: '—', icon: FileText, color: 'warning' as const },
    { label: 'Reports', value: '—', icon: FileBarChart, color: 'default' as const },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Welcome back, {user?.full_name || 'Appraiser'}
        </h1>
        <p className="text-muted-foreground">Here&apos;s your valuation overview.</p>
      </div>

      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <Badge variant={stat.color} className="mt-1">
                <Clock className="mr-1 h-3 w-3" />
                No data yet
              </Badge>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent activity placeholder */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Building2 className="h-12 w-12 text-muted-foreground/30" />
            <p className="mt-4 text-muted-foreground">
              No recent activity. Start by adding a property or creating a valuation.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}