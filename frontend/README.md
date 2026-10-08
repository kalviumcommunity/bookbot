# React + Vite

## Backend API configuration

The frontend uses one shared API service and the build-time `VITE_API_URL` value
for all backend requests. For local development, copy `.env.example` to
`.env.local` to target `http://localhost:8000`. If the variable is unset, the
client falls back to that local URL.

The repository-root `netlify.toml` sets Netlify's base directory to `frontend`,
runs `npm run build` there, publishes `dist`, and sets `VITE_API_URL` to
`https://bookbot-2dcu.onrender.com` during the build. If configuring these
settings in the Netlify UI instead, use:

- Base directory: `frontend`
- Build command: `npm run build`
- Publish directory: `dist` (relative to the base directory)
- Build environment variable: `VITE_API_URL=https://bookbot-2dcu.onrender.com`

Any Netlify UI override for `VITE_API_URL` must use the same production URL and
be enabled for the production deploy context.

Run `npm run dev` for local development and `npm run build` to verify a production
build.

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
