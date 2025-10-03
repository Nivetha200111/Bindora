'use client';

import { Drug } from '@/types';
import { DrugCard } from './DrugCard';
import { Skeleton } from '@/components/ui/skeleton';

interface DrugGridProps {
  drugs: Drug[];
  isLoading?: boolean;
  onViewDetails?: (drug: Drug) => void;
}

export function DrugGrid({ drugs, isLoading, onViewDetails }: DrugGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="space-y-4">
            <Skeleton className="h-[400px] w-full" />
          </div>
        ))}
      </div>
    );
  }

  if (drugs.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No drugs found. Try a different search.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {drugs.map((drug) => (
        <DrugCard 
          key={drug.chembl_id} 
          drug={drug} 
          onViewDetails={onViewDetails}
        />
      ))}
    </div>
  );
}

