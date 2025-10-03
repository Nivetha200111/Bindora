# DrugMatcher - Frontend

Modern Next.js dashboard for AI-powered drug discovery platform.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ or higher
- npm or yarn package manager

### Installation

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Set up environment variables:**
```bash
# Copy example env file (Windows)
copy .env.example .env.local

# macOS/Linux
cp .env.example .env.local

# Edit .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. **Start development server:**
```bash
npm run dev
```

The app will be available at http://localhost:3000

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js app router pages
│   │   ├── page.tsx           # Home page
│   │   ├── results/
│   │   │   └── page.tsx       # Results page
│   │   ├── layout.tsx         # Root layout
│   │   └── globals.css        # Global styles
│   ├── components/
│   │   ├── ui/                # Shadcn UI components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   └── ...
│   │   ├── layout/            # Layout components
│   │   │   ├── Header.tsx
│   │   │   └── Footer.tsx
│   │   ├── search/            # Search components
│   │   │   ├── SearchForm.tsx
│   │   │   └── SearchBar.tsx
│   │   └── results/           # Results components
│   │       ├── DrugCard.tsx
│   │       ├── DrugGrid.tsx
│   │       └── DrugDetailModal.tsx
│   ├── lib/
│   │   ├── api.ts             # API client
│   │   └── utils.ts           # Utility functions
│   └── types/
│       └── index.ts           # TypeScript types
├── public/                     # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## 🎨 Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Shadcn/ui
- **Icons**: Lucide React
- **HTTP**: Native Fetch API

## 📱 Features

### Home Page
- Hero section with tagline
- Platform statistics
- Search form with 3 input modes (Gene, Disease, Sequence)
- How it works section
- Technology showcase

### Search Form
- Tab-based interface for different query types
- Form validation
- Loading states
- Error handling

### Results Page
- Drug card grid layout
- Binding score visualization
- Molecular property display
- Clinical phase badges
- Pagination support
- Export functionality

### Drug Detail Modal
- Comprehensive drug information
- Tabbed interface (Overview, Properties, Binding, Clinical)
- Lipinski rule checking
- SMILES and InChI display
- Link to ChEMBL database

## 🎨 Design System

### Colors
- **Primary**: Blue (#3B82F6)
- **Secondary**: Indigo (#6366F1)
- **Success**: Green (#10B981)
- **Muted**: Gray shades

### Typography
- **Font Family**: Inter
- **Headings**: Bold, tracking-tight
- **Body**: Regular, comfortable line height

### Components
All UI components follow Shadcn/ui design system:
- Consistent border radius
- Subtle shadows
- Smooth transitions
- Accessible focus states

## 🔌 API Integration

The frontend connects to the FastAPI backend via the API client (`src/lib/api.ts`).

### Environment Variable
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### API Functions
```typescript
// Search for drugs
const results = await searchDrugs({
  query: 'BRCA1',
  queryType: 'gene',
  maxResults: 20
});

// Get drug details
const details = await getDrugDetails('CHEMBL25');

// Get platform stats
const stats = await getStats();
```

## 🧪 Development

### Available Scripts

```bash
# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linter
npm run lint
```

### Adding New Components

1. **Create component file:**
```bash
# Example: src/components/features/NewComponent.tsx
```

2. **Use TypeScript and follow conventions:**
```typescript
'use client'; // If using hooks

import { ComponentProps } from '@/types';

export function NewComponent({ prop }: ComponentProps) {
  return <div>...</div>;
}
```

3. **Import and use:**
```typescript
import { NewComponent } from '@/components/features/NewComponent';
```

## 📦 Building for Production

```bash
# Build optimized production bundle
npm run build

# Test production build locally
npm run start
```

## 🚢 Deployment

### Vercel (Recommended)

1. **Push to GitHub**
2. **Import project in Vercel**
3. **Set environment variable:**
   - `NEXT_PUBLIC_API_URL`: Your backend API URL
4. **Deploy!**

### Other Platforms

The app can be deployed to any platform that supports Next.js:
- **Netlify**: Works great with Next.js
- **Railway**: Full-stack support
- **AWS Amplify**: Enterprise scale
- **DigitalOcean App Platform**: Simple deployment

## 🎯 Usage Examples

### Search by Gene
1. Go to home page
2. Select "Gene" tab
3. Enter gene symbol (e.g., "BRCA1")
4. Click "Find Drugs"
5. View results

### Search by Sequence
1. Select "Sequence" tab
2. Paste amino acid sequence
3. Click "Find Drugs"
4. Explore drug candidates

### View Drug Details
1. On results page, click any drug card
2. Click "View Details"
3. Explore tabs (Overview, Properties, Binding, Clinical)
4. Export report or view on ChEMBL

## 🔧 Troubleshooting

### API Connection Issues
```bash
# Check if backend is running
curl http://localhost:8000/health

# Verify environment variable
echo $NEXT_PUBLIC_API_URL
```

### Build Errors
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules
npm install

# Rebuild
npm run build
```

### Type Errors
```bash
# Check TypeScript
npm run build

# Fix automatically (if possible)
npm run lint --fix
```

## 🤝 Contributing

1. Follow existing code style
2. Use TypeScript types
3. Keep components small and focused
4. Add comments for complex logic
5. Test on multiple screen sizes

## 📝 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- **Shadcn/ui**: Beautiful UI components
- **Vercel**: Next.js framework and hosting
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide**: Icon library

---

**Need Help?**
- Check the main README in the project root
- Review the API documentation at http://localhost:8000/docs
- Open an issue on GitHub

