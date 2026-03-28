# InventorySystem

This project is prepared for deployment on Render using:

- a free Python web service
- a free Postgres database
- Gunicorn for app startup
- WhiteNoise for static files

## Local development

The current Django settings still support local MySQL with:

- database name: `InventoryProjectDB`
- username: `root`
- password: `root`
- host: `localhost`
- port: `3306`

If `DATABASE_URL` is present, Django will automatically use that database instead. This is what Render uses for deployment.

## Render deployment

1. Create a GitHub repository and push this project.
2. Create a new Render Blueprint deployment from the repository.
3. Render will read `render.yaml` and create:
   - one free web service
   - one free Postgres database
4. After the first deploy, open the generated Render URL.

## Important note about free Render databases

Render free services are suitable for demos and testing. Free resources may sleep or have usage limits, so they are not ideal for production workloads.

## Manual Render settings

If you do not want to use the blueprint, use these values manually:

- Build Command: `./build.sh`
- Start Command: `cd InventoryProject && gunicorn InventoryProject.wsgi:application`
- Environment variables:
  - `PYTHON_VERSION=3.13.3`
  - `DJANGO_DEBUG=false`
  - `DJANGO_SECRET_KEY=<generate a strong value>`
  - `DATABASE_URL=<Render Postgres connection string>`
