# React + Vite

## Backend API configuration

The frontend uses `VITE_API_URL` for all backend requests. For local development,
copy `.env.example` to `.env.local` to target `http://localhost:8000`. If the
variable is unset, the client safely falls back to that local URL.

For Netlify, set the build environment variable `VITE_API_URL` to
`https://bookbot-2dcu.onrender.com` so deployed requests go to the production API.

Run `npm run dev` for local development and `npm run build` to verify a production
build.

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
