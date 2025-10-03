'use client';

import Link from 'next/link';
import { Github, Twitter } from 'lucide-react';

export function Footer() {
  return (
    <footer className="border-t py-8 bg-muted/50">
      <div className="container">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-3">
            <h3 className="text-sm font-semibold">About</h3>
            <p className="text-sm text-muted-foreground">
              AI-powered drug discovery platform for predicting drug-target interactions.
            </p>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-semibold">Resources</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="hover:text-primary">
                  API Documentation
                </a>
              </li>
              <li>
                <Link href="/" className="hover:text-primary">
                  Getting Started
                </Link>
              </li>
            </ul>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-semibold">Data Sources</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <a href="https://www.ebi.ac.uk/chembl/" target="_blank" rel="noopener noreferrer" className="hover:text-primary">
                  ChEMBL
                </a>
              </li>
              <li>
                <a href="https://www.uniprot.org/" target="_blank" rel="noopener noreferrer" className="hover:text-primary">
                  UniProt
                </a>
              </li>
            </ul>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-semibold">Connect</h3>
            <div className="flex space-x-4">
              <a href="#" className="text-muted-foreground hover:text-primary">
                <Github className="h-5 w-5" />
              </a>
              <a href="#" className="text-muted-foreground hover:text-primary">
                <Twitter className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t text-center text-sm text-muted-foreground">
          <p>© 2024 DrugMatcher. Built for educational purposes. Data from public databases.</p>
        </div>
      </div>
    </footer>
  );
}

