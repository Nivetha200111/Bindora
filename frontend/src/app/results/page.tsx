'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { searchDrugs } from '@/lib/api';
import { Drug, QueryType } from '@/types';
import { DrugGrid } from '@/components/results/DrugGrid';
import { DrugDetailModal } from '@/components/results/DrugDetailModal';
import { SearchBar } from '@/components/search/SearchBar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Download, SlidersHorizontal } from 'lucide-react';
import Link from 'next/link';

function ResultsPageContent() {
  const searchParams = useSearchParams();
  const [drugs, setDrugs] = useState<Drug[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDrug, setSelectedDrug] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [queryType, setQueryType] = useState<QueryType>('gene');

  useEffect(() => {
    const q = searchParams.get('q');
    const type = searchParams.get('type') as QueryType;

    if (q && type) {
      setQuery(q);
      setQueryType(type);
      performSearch(q, type);
    } else {
      setIsLoading(false);
    }
  }, [searchParams]);

  async function performSearch(searchQuery: string, searchType: QueryType) {
    setIsLoading(true);
    setError(null);

    try {
      const response = await searchDrugs({
        query: searchQuery,
        queryType: searchType,
        maxResults: 20,
      });
      setDrugs(response.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setIsLoading(false);
    }
  }

  const handleNewSearch = (newQuery: string) => {
    performSearch(newQuery, queryType);
  };

  return (
    <div className="container py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <Link href="/" className="inline-flex items-center text-sm text-muted-foreground hover:text-primary mb-2">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Home
          </Link>
          <h1 className="text-3xl font-bold">Search Results</h1>
          {query && (
            <p className="text-muted-foreground mt-1">
              Showing results for: <span className="font-semibold">{query}</span>
              <Badge className="ml-2" variant="secondary">{queryType}</Badge>
            </p>
          )}
        </div>

        <div className="flex gap-2">
          <Button variant="outline">
            <SlidersHorizontal className="mr-2 h-4 w-4" />
            Filters
          </Button>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Search Bar */}
      <Card>
        <CardContent className="pt-6">
          <SearchBar
            onSearch={handleNewSearch}
            placeholder={`Search for ${queryType}...`}
            defaultValue={query}
          />
        </CardContent>
      </Card>

      {/* Results Summary */}
      {!isLoading && !error && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              Found {drugs.length} potential drug candidates
            </CardTitle>
          </CardHeader>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="text-destructive">
              <p className="font-semibold">Search Error</p>
              <p className="text-sm mt-1">{error}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Grid */}
      <DrugGrid
        drugs={drugs}
        isLoading={isLoading}
        onViewDetails={(drug) => setSelectedDrug(drug.chembl_id)}
      />

      {/* Empty State */}
      {!isLoading && !error && drugs.length === 0 && query && (
        <Card>
          <CardContent className="pt-12 pb-12 text-center">
            <p className="text-muted-foreground mb-4">
              No results found for &quot;{query}&quot;
            </p>
            <Link href="/">
              <Button>Try a New Search</Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Initial State */}
      {!isLoading && !query && (
        <Card>
          <CardContent className="pt-12 pb-12 text-center">
            <p className="text-muted-foreground mb-4">
              Enter a search query to find drug candidates
            </p>
            <Link href="/">
              <Button>Go to Search</Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Drug Detail Modal */}
      {selectedDrug && (
        <DrugDetailModal
          chemblId={selectedDrug}
          onClose={() => setSelectedDrug(null)}
        />
      )}
    </div>
  );
}

export default function ResultsPage() {
  return (
    <Suspense fallback={<div className="container py-8">Loading...</div>}>
      <ResultsPageContent />
    </Suspense>
  );
}

