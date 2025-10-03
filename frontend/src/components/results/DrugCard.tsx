'use client';

import { Drug } from '@/types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ChevronRight, Pill } from 'lucide-react';
import { getClinicalPhaseLabel, getClinicalPhaseColor, formatNumber } from '@/lib/utils';

interface DrugCardProps {
  drug: Drug;
  onViewDetails?: (drug: Drug) => void;
}

export function DrugCard({ drug, onViewDetails }: DrugCardProps) {
  const bindingScoreColor = drug.binding_score >= 80 
    ? 'bg-green-500' 
    : drug.binding_score >= 60 
    ? 'bg-blue-500' 
    : 'bg-gray-500';

  return (
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-2">
            <Pill className="h-5 w-5 text-primary" />
            <div>
              <CardTitle className="text-lg">{drug.name || 'Unknown Drug'}</CardTitle>
              <CardDescription className="text-xs">{drug.chembl_id}</CardDescription>
            </div>
          </div>
          <Badge className={getClinicalPhaseColor(drug.clinical_phase)}>
            {getClinicalPhaseLabel(drug.clinical_phase)}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Binding Score */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Binding Score</span>
            <span className="font-semibold">{formatNumber(drug.binding_score, 1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`${bindingScoreColor} h-2 rounded-full transition-all`}
              style={{ width: `${drug.binding_score}%` }}
            />
          </div>
        </div>

        {/* Properties Grid */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-muted-foreground text-xs">Molecular Weight</p>
            <p className="font-medium">{formatNumber(drug.molecular_weight, 0)} Da</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">LogP</p>
            <p className="font-medium">{formatNumber(drug.logp, 2)}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">H-Bond Donors</p>
            <p className="font-medium">{drug.hbd}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">H-Bond Acceptors</p>
            <p className="font-medium">{drug.hba}</p>
          </div>
        </div>

        {/* Drug-likeness Badge */}
        {drug.is_drug_like && (
          <Badge variant="secondary" className="bg-green-100 text-green-800">
            ✓ Drug-like (Lipinski)
          </Badge>
        )}

        {/* SMILES */}
        <div className="text-xs">
          <p className="text-muted-foreground mb-1">SMILES</p>
          <p className="font-mono text-xs bg-muted p-2 rounded truncate" title={drug.smiles}>
            {drug.smiles}
          </p>
        </div>
      </CardContent>

      <CardFooter>
        <Button 
          variant="outline" 
          className="w-full" 
          onClick={() => onViewDetails?.(drug)}
        >
          View Details
          <ChevronRight className="ml-2 h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}

