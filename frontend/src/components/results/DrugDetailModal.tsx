'use client';

import { useEffect, useState } from 'react';
import { DrugDetails } from '@/types';
import { getDrugDetails } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { X, ExternalLink, Download } from 'lucide-react';
import { getClinicalPhaseLabel, getClinicalPhaseColor, formatNumber } from '@/lib/utils';

interface DrugDetailModalProps {
  chemblId: string;
  onClose: () => void;
}

export function DrugDetailModal({ chemblId, onClose }: DrugDetailModalProps) {
  const [drug, setDrug] = useState<DrugDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDrugDetails() {
      try {
        setIsLoading(true);
        const details = await getDrugDetails(chemblId);
        setDrug(details);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load drug details');
      } finally {
        setIsLoading(false);
      }
    }

    loadDrugDetails();
  }, [chemblId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto m-4">
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <CardTitle className="text-2xl">
                  {isLoading ? <Skeleton className="h-8 w-64" /> : drug?.name || 'Unknown Drug'}
                </CardTitle>
                <CardDescription>
                  {isLoading ? <Skeleton className="h-4 w-32" /> : drug?.chembl_id}
                </CardDescription>
              </div>
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="h-5 w-5" />
              </Button>
            </div>
          </CardHeader>

          <CardContent>
            {error && (
              <div className="text-destructive bg-destructive/10 p-4 rounded-md mb-4">
                {error}
              </div>
            )}

            {isLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-64 w-full" />
                <Skeleton className="h-32 w-full" />
              </div>
            ) : drug ? (
              <Tabs defaultValue="overview" className="space-y-4">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="properties">Properties</TabsTrigger>
                  <TabsTrigger value="binding">Binding</TabsTrigger>
                  <TabsTrigger value="clinical">Clinical</TabsTrigger>
                </TabsList>

                {/* Overview Tab */}
                <TabsContent value="overview" className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-2">Description</h3>
                    <p className="text-sm text-muted-foreground">
                      {drug.description || 'No description available.'}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h3 className="font-semibold mb-2">Clinical Status</h3>
                      <Badge className={getClinicalPhaseColor(drug.clinical_phase)}>
                        {getClinicalPhaseLabel(drug.clinical_phase)}
                      </Badge>
                    </div>
                    <div>
                      <h3 className="font-semibold mb-2">Drug-likeness</h3>
                      <Badge variant={drug.is_drug_like ? 'default' : 'secondary'}>
                        {drug.is_drug_like ? '✓ Passes Lipinski' : '✗ Fails Lipinski'}
                      </Badge>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold mb-2">SMILES Notation</h3>
                    <p className="text-xs font-mono bg-muted p-3 rounded break-all">
                      {drug.smiles}
                    </p>
                  </div>

                  {drug.inchi_key && (
                    <div>
                      <h3 className="font-semibold mb-2">InChI Key</h3>
                      <p className="text-xs font-mono bg-muted p-3 rounded">
                        {drug.inchi_key}
                      </p>
                    </div>
                  )}
                </TabsContent>

                {/* Properties Tab */}
                <TabsContent value="properties" className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-3">Molecular Properties</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <PropertyItem label="Molecular Weight" value={`${formatNumber(drug.molecular_weight, 2)} Da`} />
                      <PropertyItem label="LogP" value={formatNumber(drug.logp, 2)} />
                      <PropertyItem label="H-Bond Donors" value={drug.hbd.toString()} />
                      <PropertyItem label="H-Bond Acceptors" value={drug.hba.toString()} />
                      <PropertyItem label="TPSA" value={`${formatNumber(drug.tpsa, 2)} Ų`} />
                      {drug.properties.num_rotatable_bonds !== undefined && (
                        <PropertyItem label="Rotatable Bonds" value={drug.properties.num_rotatable_bonds.toString()} />
                      )}
                      {drug.properties.num_aromatic_rings !== undefined && (
                        <PropertyItem label="Aromatic Rings" value={drug.properties.num_aromatic_rings.toString()} />
                      )}
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold mb-3">Lipinski&apos;s Rule of Five</h3>
                    <div className="space-y-2">
                      <RuleCheck 
                        passed={drug.molecular_weight < 500} 
                        label="Molecular weight < 500 Da"
                        value={formatNumber(drug.molecular_weight, 0)}
                      />
                      <RuleCheck 
                        passed={drug.logp < 5} 
                        label="LogP < 5"
                        value={formatNumber(drug.logp, 2)}
                      />
                      <RuleCheck 
                        passed={drug.hbd <= 5} 
                        label="H-bond donors ≤ 5"
                        value={drug.hbd.toString()}
                      />
                      <RuleCheck 
                        passed={drug.hba <= 10} 
                        label="H-bond acceptors ≤ 10"
                        value={drug.hba.toString()}
                      />
                    </div>
                  </div>
                </TabsContent>

                {/* Binding Tab */}
                <TabsContent value="binding" className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-3">Binding Score</h3>
                    <div className="flex items-center space-x-4">
                      <div className="text-4xl font-bold text-primary">
                        {formatNumber(drug.binding_score, 1)}%
                      </div>
                      <div className="flex-1">
                        <div className="w-full bg-gray-200 rounded-full h-4">
                          <div
                            className="bg-primary h-4 rounded-full"
                            style={{ width: `${drug.binding_score}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {drug.similar_drugs && drug.similar_drugs.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3">Similar Drugs</h3>
                      <div className="space-y-2">
                        {drug.similar_drugs.map((similarId) => (
                          <Badge key={similarId} variant="outline">
                            {similarId}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </TabsContent>

                {/* Clinical Tab */}
                <TabsContent value="clinical" className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-2">Clinical Phase</h3>
                    <Badge className={getClinicalPhaseColor(drug.clinical_phase)}>
                      {getClinicalPhaseLabel(drug.clinical_phase)}
                    </Badge>
                  </div>

                  {drug.clinical_trials && drug.clinical_trials.length > 0 ? (
                    <div>
                      <h3 className="font-semibold mb-3">Clinical Trials</h3>
                      <div className="space-y-3">
                        {drug.clinical_trials.map((trial) => (
                          <Card key={trial.nct_id}>
                            <CardContent className="pt-4">
                              <h4 className="font-medium mb-1">{trial.title}</h4>
                              <div className="flex gap-2 text-sm text-muted-foreground">
                                <Badge variant="outline">{trial.phase}</Badge>
                                <Badge variant="outline">{trial.status}</Badge>
                                <span>{trial.nct_id}</span>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No clinical trial data available.</p>
                  )}
                </TabsContent>
              </Tabs>
            ) : null}

            {/* Action Buttons */}
            {drug && (
              <div className="flex gap-2 mt-6 pt-6 border-t">
                <Button variant="outline" className="flex-1">
                  <Download className="mr-2 h-4 w-4" />
                  Export Report
                </Button>
                <Button variant="outline" className="flex-1" asChild>
                  <a 
                    href={`https://www.ebi.ac.uk/chembl/compound_report_card/${drug.chembl_id}/`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <ExternalLink className="mr-2 h-4 w-4" />
                    View on ChEMBL
                  </a>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function PropertyItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-muted p-3 rounded">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className="font-semibold">{value}</p>
    </div>
  );
}

function RuleCheck({ passed, label, value }: { passed: boolean; label: string; value: string }) {
  return (
    <div className="flex items-center justify-between p-3 bg-muted rounded">
      <div className="flex items-center space-x-2">
        <span className={passed ? 'text-green-600' : 'text-red-600'}>
          {passed ? '✓' : '✗'}
        </span>
        <span className="text-sm">{label}</span>
      </div>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}

