# MLE-STAR Frontend

A React/Next.js frontend for the MLE-STAR (Machine Learning Engineering Agent via Search and Targeted Refinement) system.

## Features

- Task input interface with configuration panel
- Real-time pipeline visualization
- Agent graph showing execution flow
- Execution controls (start/pause/stop)
- Live log viewer
- Results display with code viewer
- Submission preview and download

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js app router
│   │   ├── api/               # API routes
│   │   ├── globals.css        # Global styles
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Main page
│   ├── components/
│   │   ├── execution/         # Execution controls
│   │   ├── layout/            # Layout components
│   │   ├── pipeline/          # Pipeline visualization
│   │   ├── results/           # Results display
│   │   ├── submission/        # Submission components
│   │   └── task/              # Task input components
│   └── types/                 # TypeScript types
├── package.json
├── tailwind.config.ts
└── tsconfig.json
```

## Configuration

The frontend connects to the Python backend at `http://localhost:8000` by default. Configure the backend URL using the `BACKEND_URL` environment variable.

## License

MIT
