# Deployment

## Free Vercel Frontend

The static review console can run on Vercel's free tier.

Recommended Vercel settings:

- Framework preset: Other
- Build command: leave empty
- Output directory: `frontend/web`

This deploys the frontend only. The Python backend is a long-running local
service and should be reviewed with Docker or local Python.

## Docker Backend And Frontend

Use Docker Compose for the full local review environment:

```bash
docker compose up --build
```

Services:

- `web`: static frontend on port `4173`
- `backend`: Python API on port `8088`

