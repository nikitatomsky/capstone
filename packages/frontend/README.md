# Assignment Dashboard Frontend

React Single Page Application (SPA) for the admin assignment dashboard. Displays assignments, allows creation of new assignments, and shows real-time status updates using Server-Sent Events (SSE).

## Tech Stack

- **Framework**: React 18
- **Build Tool**: Vite
- **Language**: TypeScript
- **Routing**: React Router
- **Styling**: Native CSS (inline styles for MVP)
- **Real-time Updates**: Server-Sent Events (SSE)

## Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:4000`

## Getting Started

### Install Dependencies

```bash
npm install
```

### Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
src/
├── components/           # React components
│   ├── AssignmentList.tsx       # List all assignments with real-time updates
│   ├── AssignmentDetail.tsx     # View single assignment details
│   └── CreateAssignmentForm.tsx # Create new assignment
├── services/            # API and SSE clients
│   ├── api.ts          # REST API client
│   └── sse.ts          # Server-Sent Events client
├── types/              # TypeScript type definitions
│   └── models.ts       # Backend API model interfaces
├── App.tsx             # Main app with router
└── main.tsx            # Entry point
```

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run linter

## Features

### Assignment List
- Displays all assignments from backend
- Real-time updates via SSE when assignment status changes
- Links to assignment detail view
- Shows status and priority for each assignment

### Assignment Detail
- View full details of a single assignment
- Shows technician info, description, timestamps
- Links back to assignment list

### Create Assignment
- Form to create new assignments
- Select technician from dropdown (fetched from backend)
- Set title, description, and priority
- Redirects to assignment list after creation

## Backend Dependency

The frontend requires the FastAPI backend to be running on `http://localhost:4000`. Start the backend first:

```bash
cd ../api
poetry run uvicorn app.main:app --reload --port 4000
```

## API Endpoints Used

- `GET /api/assignments` - Fetch all assignments
- `GET /api/assignments/{id}` - Fetch single assignment
- `POST /api/assignments` - Create new assignment
- `GET /api/technicians` - Fetch all technicians
- `GET /api/assignments/stream` - SSE stream for real-time updates

## CORS Configuration

The backend must have CORS enabled for `http://localhost:5173`. This is configured in the backend's CORS middleware.

## Real-time Updates

The app uses Server-Sent Events (SSE) to receive real-time assignment updates from the backend. When a technician responds via Telegram, the assignment status is automatically updated in the UI without page refresh.

## Future Enhancements

- Authentication and authorization
- Enhanced styling with a component library (e.g., Material-UI, Tailwind)
- Error boundaries for better error handling
- Loading states and skeleton screens
- Optimistic UI updates
- Assignment filtering and search
- Pagination for large assignment lists

