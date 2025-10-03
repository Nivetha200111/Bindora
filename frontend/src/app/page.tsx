'use client';

import { useEffect, useState } from 'react';
import { SearchForm } from '@/components/search/SearchForm';
import { Card, CardContent } from '@/components/ui/card';
import { Beaker, Target, TrendingUp, Sparkles } from 'lucide-react';
import { getStats } from '@/lib/api';

export default function HomePage() {
  const [stats, setStats] = useState({
    total_drugs: 3000,
    total_targets: 20000,
    predictions_made: 150000,
  });

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await getStats();
        setStats(data);
      } catch (err) {
        console.error('Failed to load stats:', err);
      }
    }
    loadStats();
  }, []);

  return (
    <div className="container py-12 space-y-12">
      {/* Hero Section */}
      <section className="text-center space-y-6">
        <div className="space-y-4">
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
            AI-Powered Drug Discovery
          </h1>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Predict drug-target interactions using advanced machine learning.
            Accelerate your drug discovery research with instant predictions.
          </p>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto pt-8">
          <StatCard
            icon={<Beaker className="h-6 w-6 text-blue-600" />}
            value={stats.total_drugs.toLocaleString()}
            label="Drugs Analyzed"
          />
          <StatCard
            icon={<Target className="h-6 w-6 text-indigo-600" />}
            value={stats.total_targets.toLocaleString()}
            label="Protein Targets"
          />
          <StatCard
            icon={<TrendingUp className="h-6 w-6 text-purple-600" />}
            value={stats.predictions_made.toLocaleString()}
            label="Predictions Made"
          />
        </div>
      </section>

      {/* Search Section */}
      <section className="max-w-2xl mx-auto space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-semibold">Start Your Search</h2>
          <p className="text-muted-foreground">
            Enter a disease, gene symbol, or protein sequence to find potential drug candidates
          </p>
        </div>
        <SearchForm />
      </section>

      {/* Features Section */}
      <section className="max-w-5xl mx-auto pt-12">
        <h2 className="text-3xl font-bold text-center mb-8">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <FeatureCard
            icon={<Target className="h-8 w-8 text-primary" />}
            title="1. Select Target"
            description="Search by disease, gene symbol, or provide a protein sequence directly"
          />
          <FeatureCard
            icon={<Sparkles className="h-8 w-8 text-primary" />}
            title="2. AI Analysis"
            description="Our models predict binding affinity between drugs and your target protein"
          />
          <FeatureCard
            icon={<Beaker className="h-8 w-8 text-primary" />}
            title="3. Get Results"
            description="View ranked drug candidates with detailed molecular properties and clinical data"
          />
        </div>
      </section>

      {/* Technology Section */}
      <section className="max-w-4xl mx-auto pt-12">
        <Card className="bg-gradient-to-br from-blue-50 to-indigo-50">
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <h3 className="text-2xl font-bold">Powered by Advanced AI</h3>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                We use state-of-the-art protein language models (ESM-2) and molecular fingerprinting (RDKit)
                to predict drug-target interactions. All data sourced from ChEMBL, UniProt, and BindingDB.
              </p>
              <div className="flex flex-wrap justify-center gap-3 pt-4">
                <TechBadge label="PyTorch" />
                <TechBadge label="Transformers" />
                <TechBadge label="RDKit" />
                <TechBadge label="ChEMBL" />
                <TechBadge label="UniProt" />
                <TechBadge label="Next.js" />
                <TechBadge label="FastAPI" />
              </div>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function StatCard({ icon, value, label }: { icon: React.ReactNode; value: string; label: string }) {
  return (
    <Card>
      <CardContent className="pt-6 text-center space-y-2">
        <div className="flex justify-center">{icon}</div>
        <div className="text-3xl font-bold">{value}</div>
        <div className="text-sm text-muted-foreground">{label}</div>
      </CardContent>
    </Card>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <Card className="text-center">
      <CardContent className="pt-6 space-y-3">
        <div className="flex justify-center">{icon}</div>
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

function TechBadge({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary/10 text-primary">
      {label}
    </span>
  );
}

