# Render Deployment Guide

This setup is optimized for a college presentation:

- One free Render web service
- One free external MySQL database
- Demo mode enabled with `AUTH_DISABLED=true`
- Tesseract OCR fallback instead of PaddleOCR for a lighter build

## 1. Push this repo to GitHub

Make sure these files are committed:

- `Dockerfile`
- `render.yaml`
- `requirements-render.txt`

## 2. Create a free MySQL database

Use a free MySQL host such as Aiven MySQL Free Tier.

Create a database and copy the connection string in this format:

```text
mysql://USER:PASSWORD@HOST:PORT/DATABASE
```

If your password contains special characters, URL-encode it before saving.

## 3. Deploy to Render

1. Go to Render.
2. Click `New` -> `Blueprint`.
3. Connect your GitHub repo.
4. Render will detect `render.yaml`.
5. When prompted, set `MYSQL_URL` to your database connection string.
6. Create the service and wait for the build to finish.

## 4. Open the app

After deploy:

1. Open the Render app URL.
2. The Streamlit frontend should load.
3. The backend will auto-start inside the same container.
4. Because `AUTH_DISABLED=true`, the UI should enter demo mode without login.

## 5. Presentation-day tips

- Open the app 5 to 10 minutes before the presentation because free Render services sleep after inactivity.
- Use 1 or 2 small sample invoices for a smoother demo.
- Prefer JPG or PNG for the fastest OCR demo.
- Do not rely on uploaded files staying forever. Free services can lose local files on redeploy.

## Troubleshooting

If the app page opens but says backend is offline:

- Check Render logs for MySQL connection errors.
- Verify `MYSQL_URL` is correct.
- Make sure the database is reachable from Render.

If OCR is too slow:

- Use a smaller image instead of a large PDF.
- Try a cleaner invoice sample with clear printed text.
