# FlowLogic RouteAI Frontend

A modern, production-grade React frontend for the FlowLogic RouteAI autonomous truck routing system.

## 🚀 Features

- **Modular Architecture**: Clean separation of concerns with components, hooks, and utilities
- **TypeScript**: Full type safety throughout the application
- **Tailwind CSS**: Modern, responsive design system
- **State Management**: Zustand for efficient global state management
- **AI Chat Interface**: Natural language constraint input with intelligent responses
- **Address Input**: Multiple input methods (manual, paste, CSV upload)
- **Route Visualization**: Interactive map display with route overlays
- **Export Capabilities**: CSV and PDF export with customizable options
- **Responsive Design**: Mobile-first approach with tablet and desktop optimization
- **Accessibility**: WCAG compliant with keyboard navigation and screen reader support

## 🏗️ Architecture

```
src/
├── components/           # React components
│   ├── Layout/          # Layout components (Header, Sidebar, etc.)
│   ├── Chat/            # Chat interface components
│   ├── Input/           # Address and constraint input components
│   ├── Map/             # Route visualization components
│   ├── Results/         # Results display and export components
│   └── Welcome/         # Welcome screen component
├── hooks/               # Custom React hooks
│   ├── useRouting.ts    # API integration for routing
│   └── useExport.ts     # Export functionality
├── store/               # State management
│   └── useAppStore.ts   # Zustand store configuration
├── types/               # TypeScript type definitions
│   └── index.ts         # Application types
├── utils/               # Utility functions
│   └── cn.ts            # Class name utility
└── App.tsx              # Main application component
```

## 🛠️ Setup & Installation

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running (see main README)

### Installation

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Environment setup:**
   Create a `.env` file in the frontend directory:
   ```env
   REACT_APP_API_URL=http://localhost:8000
   REACT_APP_MAPBOX_TOKEN=your_mapbox_token_here
   ```

3. **Start development server:**
   ```bash
   npm start
   ```

4. **Build for production:**
   ```bash
   npm run build
   ```

## 📱 Components Overview

### Layout Components

- **Header**: Navigation tabs, loading indicators, mobile menu
- **Sidebar**: Input forms and chat interface (collapsible on mobile)
- **MainContent**: Dynamic content area based on active tab

### Chat Components

- **ChatInput**: AI-powered constraint input with natural language processing
- Real-time chat interface with typing indicators
- Smart response generation for routing constraints
- Quick prompt suggestions for common scenarios

### Input Components

- **AddressInput**: Multi-method address input
  - Manual text entry with example prompts
  - Clipboard paste functionality
  - CSV file upload with validation
  - Depot address and constraint configuration

### Map Components

- **RouteMap**: Interactive route visualization
  - Mock map implementation for development
  - Route path rendering with truck-specific colors
  - Interactive legend and layer controls
  - Zoom controls and route statistics overlay
  - Ready for Mapbox GL JS integration

### Results Components

- **ResultsSummary**: Comprehensive route analysis
  - Key performance metrics dashboard
  - Individual route details with utilization bars
  - Stop-by-stop breakdown with ETAs
  - AI analysis and recommendations display

- **ExportModal**: Flexible export options
  - CSV export with detailed route data
  - PDF export with visual formatting
  - Configurable export options (map, summary inclusion)
  - Progress indicators and error handling

## 🔧 State Management

Uses Zustand for efficient state management:

```typescript
interface AppState {
  // Input data
  addresses: string;
  constraints: string;
  depotAddress: string;
  
  // Results
  currentRoutes: TruckRoute[];
  routingSummary: string;
  
  // UI state
  activeTab: 'input' | 'results' | 'map';
  isLoading: boolean;
  chatHistory: ChatMessage[];
  
  // Actions
  setAddresses: (addresses: string) => void;
  performRouting: () => Promise<void>;
  // ... other actions
}
```

## 🌐 API Integration

### Autonomous Routing

```typescript
const { performAutonomousRouting } = useRouting();

await performAutonomousRouting(
  addresses,
  constraints,
  depotAddress
);
```

### File Upload Routing

```typescript
const { uploadAndRoute } = useRouting();

await uploadAndRoute(
  stopsFile,
  trucksFile,
  constraints
);
```

## 📤 Export Functionality

### CSV Export
- Route summary with key metrics
- Detailed stop-by-stop data
- AI analysis and recommendations
- Compatible with Excel and Google Sheets

### PDF Export
- Executive summary with charts
- Visual route breakdown
- Performance metrics
- Map visualization (when integrated)
- Professional formatting for reports

## 🎨 Design System

### Colors
- **Primary**: Blue (`#0ea5e9`) for main actions and branding
- **Success**: Green (`#22c55e`) for positive feedback
- **Warning**: Orange (`#f59e0b`) for cautions
- **Danger**: Red (`#ef4444`) for errors
- **Gray Scale**: Comprehensive gray palette for UI elements

### Typography
- **Font**: Inter (Google Fonts)
- **Weights**: 300, 400, 500, 600, 700
- **Responsive sizing** with Tailwind classes

### Spacing & Layout
- **Grid System**: Responsive CSS Grid and Flexbox
- **Containers**: Max-width constraints with centered content
- **Padding/Margins**: Consistent 4px base unit (Tailwind default)

## 📱 Responsive Design

### Breakpoints
- **Mobile**: `< 768px` - Single column, collapsible sidebar
- **Tablet**: `768px - 1024px` - Two column with adaptive sidebar
- **Desktop**: `> 1024px` - Full three-column layout

### Mobile Optimizations
- Touch-friendly button sizes (min 44px)
- Swipe-friendly chat interface
- Optimized input methods for mobile keyboards
- Progressive enhancement for advanced features

## ♿ Accessibility

- **WCAG 2.1 AA Compliance**: Color contrast, focus management
- **Keyboard Navigation**: Full keyboard access to all features
- **Screen Reader Support**: Semantic HTML and ARIA labels
- **Focus Management**: Visible focus indicators and logical tab order

## 🔌 Integration Points

### Mapbox GL JS Integration
For production deployment, replace the mock map component:

```typescript
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

// Initialize map
const map = new mapboxgl.Map({
  container: mapContainer.current,
  style: 'mapbox://styles/mapbox/streets-v11',
  center: [-84.388, 33.749], // Atlanta
  zoom: 10
});
```

### Backend API
Current endpoints used:
- `POST /route/auto` - Autonomous routing
- `POST /route/upload` - CSV file routing
- `POST /route/recalculate` - Live re-routing (future)

## 🚀 Production Deployment

### Build Optimization
```bash
npm run build
```

### Environment Variables
```env
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_MAPBOX_TOKEN=pk.your_production_token
REACT_APP_ENVIRONMENT=production
```

### Hosting Options
- **Vercel**: Zero-config deployment with automatic builds
- **Netlify**: JAMstack hosting with form handling
- **AWS S3 + CloudFront**: Scalable static hosting
- **Docker**: Containerized deployment

### Performance Considerations
- **Code Splitting**: Lazy load route components
- **Image Optimization**: WebP format with fallbacks
- **Bundle Analysis**: Use `npm run build --analyze`
- **CDN**: Serve static assets from CDN

## 🧪 Testing

### Unit Tests
```bash
npm test
```

### Component Testing
```bash
npm run test:components
```

### E2E Testing (Future)
```bash
npm run test:e2e
```

## 🔧 Development

### Code Style
- **ESLint**: Airbnb configuration
- **Prettier**: Automatic code formatting
- **TypeScript**: Strict mode enabled

### Git Hooks
- **Pre-commit**: Lint and format code
- **Pre-push**: Run tests

### Hot Reload
Development server supports hot module replacement for efficient development.

## 📦 Dependencies

### Core
- **React 18**: Latest stable React version
- **TypeScript**: Type safety and developer experience
- **Tailwind CSS**: Utility-first CSS framework

### State & Data
- **Zustand**: Lightweight state management
- **Axios**: HTTP client for API requests
- **React Hot Toast**: Toast notifications

### UI & Icons
- **Lucide React**: Modern icon library
- **Headless UI**: Unstyled, accessible components

### Export & Files
- **jsPDF**: PDF generation
- **PapaParse**: CSV parsing and generation

### Development
- **React Scripts**: Create React App toolchain
- **PostCSS**: CSS processing
- **Autoprefixer**: CSS vendor prefixes

## 🤝 Contributing

1. Follow the established folder structure
2. Use TypeScript for all new components
3. Follow the existing naming conventions
4. Add proper error handling and loading states
5. Ensure mobile responsiveness
6. Test with keyboard navigation

## 🔗 Integration with Backend

The frontend is designed to work seamlessly with the FlowLogic RouteAI backend. Ensure the backend is running on `http://localhost:8000` for development, or update the `REACT_APP_API_URL` environment variable for production deployments.