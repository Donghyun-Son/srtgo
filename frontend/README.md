# SRTgo Web Frontend

React + TypeScript frontend for SRTgo web application.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **TanStack Query** - Server state management
- **Zustand** - Client state management
- **React Hook Form** - Form handling
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **Lucide React** - Icons

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `.env` file (optional):

```env
VITE_API_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
```

The app will be available at http://localhost:3000

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable components
│   │   └── Layout.tsx    # Main layout with nav
│   ├── pages/            # Page components
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── ReservationPage.tsx
│   │   └── SettingsPage.tsx
│   ├── services/         # API services
│   │   └── api.ts        # Axios instance & API calls
│   ├── store/            # Zustand stores
│   │   ├── authStore.ts  # Auth state
│   │   └── reservationStore.ts
│   ├── hooks/            # Custom hooks (to be added)
│   ├── utils/            # Utility functions (to be added)
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

## Features

### Implemented

1. **Authentication**
   - Login / Register pages
   - JWT token management
   - Protected routes

2. **Dashboard**
   - Recent reservations list
   - Quick stats (total, completed, searching)
   - Reservation status badges

3. **Reservation**
   - 3-step wizard (Basic info → Passengers → Confirm)
   - Train type selection (SRT/KTX)
   - Station dropdowns
   - Date/time pickers
   - Passenger count inputs
   - Auto payment option

4. **Settings**
   - Train login credentials (encrypted)
   - Card information (encrypted)
   - Telegram notifications

5. **Responsive Design**
   - Mobile-first approach
   - Responsive navigation
   - Touch-friendly UI

### API Integration

All API calls are handled through `src/services/api.ts`:

- Auth: `/api/auth/*`
- Credentials: `/api/credentials/*`
- Trains: `/api/trains/*`
- Reservations: `/api/reservations/*`

## Building for Production

```bash
npm run build
```

Build output will be in `dist/` directory.

## Deployment

### Static Hosting (Netlify, Vercel, etc.)

```bash
npm run build
# Deploy the dist/ directory
```

### With Backend

Serve the `dist/` directory using a web server:

```bash
# Using Python
python -m http.server -d dist 3000

# Using Node.js (serve)
npx serve -s dist -p 3000
```

## Development Tips

### Adding New Pages

1. Create page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation link in `src/components/Layout.tsx`

### Adding New API Calls

Add to `src/services/api.ts`:

```typescript
export const myApi = {
  getData: () => api.get('/api/my-endpoint'),
  postData: (data: any) => api.post('/api/my-endpoint', data),
}
```

### State Management

- **Global auth state**: Use `useAuthStore` (persisted to localStorage)
- **API data**: Use `@tanstack/react-query`
- **Form state**: Use `react-hook-form`
- **Other global state**: Create new Zustand store

## Styling

Uses Tailwind CSS with custom components:

- `.btn` - Base button
- `.btn-primary` - Primary button
- `.btn-secondary` - Secondary button
- `.input` - Text input
- `.card` - Card container

Custom colors in `tailwind.config.js`:
- Primary: Blue shades (50-900)

## Mobile Support

The app is fully responsive with:
- Mobile-first design
- Touch-friendly buttons
- Responsive grid layouts
- Mobile navigation (bottom tabs)
- Desktop navigation (sidebar)

## Future Enhancements

- [ ] Real-time WebSocket integration for polling updates
- [ ] Train search results page
- [ ] Reservation detail page
- [ ] Push notifications
- [ ] PWA support
- [ ] Dark mode
- [ ] Internationalization (i18n)
- [ ] Unit tests
- [ ] E2E tests

## Troubleshooting

### CORS Issues
Make sure backend is configured with correct CORS origins in `backend/.env`:
```
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### API Connection Issues
Check that backend is running on port 8000 and update `VITE_API_URL` if needed.

### Build Errors
Clear node_modules and reinstall:
```bash
rm -rf node_modules package-lock.json
npm install
```
