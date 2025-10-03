'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import { QueryType } from '@/types';

interface SearchFormProps {
  onSearch?: (query: string, queryType: QueryType) => void;
}

export function SearchForm({ onSearch }: SearchFormProps) {
  const router = useRouter();
  const [queryType, setQueryType] = useState<QueryType>('gene');
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setIsLoading(true);

    try {
      if (onSearch) {
        onSearch(query, queryType);
      } else {
        // Navigate to results page with query params
        const params = new URLSearchParams({
          q: query,
          type: queryType,
        });
        router.push(`/results?${params.toString()}`);
      }
    } catch (err) {
      setError('Search failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full">
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <Tabs value={queryType} onValueChange={(value) => setQueryType(value as QueryType)}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="gene">Gene</TabsTrigger>
              <TabsTrigger value="disease">Disease</TabsTrigger>
              <TabsTrigger value="sequence">Sequence</TabsTrigger>
            </TabsList>

            <TabsContent value="gene" className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="gene-input">Gene Symbol</Label>
                <Input
                  id="gene-input"
                  placeholder="e.g., BRCA1, TP53, EGFR"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="text-base"
                />
                <p className="text-sm text-muted-foreground">
                  Enter a gene symbol to find drugs that target this protein
                </p>
              </div>
            </TabsContent>

            <TabsContent value="disease" className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="disease-input">Disease Name</Label>
                <Input
                  id="disease-input"
                  placeholder="e.g., Alzheimer's disease, Breast cancer"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="text-base"
                />
                <p className="text-sm text-muted-foreground">
                  Enter a disease name to find potential drug candidates
                </p>
              </div>
            </TabsContent>

            <TabsContent value="sequence" className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="sequence-input">Protein Sequence</Label>
                <Textarea
                  id="sequence-input"
                  placeholder="Enter amino acid sequence (e.g., MKTIIALSYIFCLVFA...)"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="font-mono text-sm min-h-[120px]"
                />
                <p className="text-sm text-muted-foreground">
                  Paste a protein sequence in FASTA or plain text format
                </p>
              </div>
            </TabsContent>
          </Tabs>

          {error && (
            <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-md">
              {error}
            </div>
          )}

          <Button type="submit" className="w-full" size="lg" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="mr-2 h-4 w-4" />
                Find Drugs
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

