# Netlify deployment

TradeMate serves its installable PWA from Netlify. A small Render web service
runs the Python API, and Neon PostgreSQL holds account, invite, session, and
lesson-progress data. The app's sign-in and invite requirements remain enabled
on the public Netlify URL.

The repository includes a Netlify build script, a same-origin API proxy
function, and a Render Blueprint. Netlify's build copies only the PWA files to
the public site; backend code and database credentials are not put in the
static deployment.

## Create the database

Create a PostgreSQL project in Neon. Copy its pooled connection string and
add `sslmode=require` if the value does not already include it. The Render API
uses this as `TRADEMATE_DATABASE_URL`. Keep the value in Render's secret
environment settings; never add it to this repository.

## Deploy the Python API

In Render, create a Blueprint from this repository and branch. The included
`render.yaml` selects a Free web service and asks you to enter these private
environment values during setup:

- `TRADEMATE_DATABASE_URL`: the Neon connection string.
- `TRADEMATE_ADMIN_EMAIL`: the owner's sign-in email.
- `TRADEMATE_ADMIN_PASSWORD`: a unique password of at least 12 characters.

The service starts with Binance as its data source. Its free instance can
sleep after 15 minutes without traffic, so the first request after idle may
take about a minute. Neon retains the database separately from Render's
temporary app filesystem. Free plans have usage limits; check the providers'
current dashboards before upgrading any resource.

After Render deploys, copy the service URL, such as
`https://trademate-api.onrender.com`.

## Deploy the PWA

In Netlify, import the same repository and deployment branch. Netlify reads
`netlify.toml`, builds the site from the `src/trademate/static` sources, and
publishes the PWA files. Set the following environment variable for the site:

- `TRADEMATE_API_ORIGIN`: the Render service URL, without a trailing path.

Trigger a deploy after saving the variable. The Netlify function forwards
`/api/*` requests to Render and keeps the browser on the Netlify origin, so
the password-protected session cookie remains first party.

The resulting `*.netlify.app` URL is public, but sign-in is still required.
Friends need one-use invite codes from the owner account before they can make
their own accounts. They can then install the site from their phone browser.

## Local build preview

From the repository root:

```powershell
npm run build
```

The generated `netlify-build` directory is ignored by Git and contains only
the static PWA shell. The API and account routes still need the configured
Render service and Neon database.
