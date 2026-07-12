# Hosting The Hero's Book

How to serve `app/` from a free static host, straight out of the private GitHub repo (`EconomicDarwin/rpg_kids_companion`, branch `main`). No build step, no framework. The only hard requirement is HTTPS, because Silk will not register the service worker (and therefore offline mode) over plain HTTP.

Primary recommendation: **Cloudflare Pages**. A shorter **Netlify** alternative is at the bottom.

A note before you start: Cloudflare now steers new projects toward "Workers with static assets" instead of classic Pages. Pages is not deprecated — existing and new Pages projects remain fully supported — but the create screen in the dashboard leads with Workers, so you may have to look for the Pages tab. For a plain static site like this one, Pages is still the simpler choice: no config file, no Worker code, just "here is my folder." If the Pages option ever disappears for new projects, the Workers static-assets path serves the same files and is also free; the key settings (no build, deploy the `app/` directory) carry over.

## 1. One-time setup on Cloudflare Pages

1. Create a free Cloudflare account at https://dash.cloudflare.com/sign-up (email + password, no card needed).
2. In the dashboard sidebar, go to **Workers & Pages**, then **Create** (or **Create application**).
3. The create screen defaults to Workers. Switch to the **Pages** tab, then choose **Connect to Git** (may be labeled **Import an existing Git repository**).
4. Choose **GitHub** and sign in when prompted. GitHub will ask you to install the Cloudflare Pages app on your account. Under **Repository access**, pick **Only select repositories** and select `EconomicDarwin/rpg_kids_companion`. Private repos work exactly like public ones here — the app install is what grants access. Click **Install & Authorize**.
5. Back in Cloudflare, select the `rpg_kids_companion` repo and click **Begin setup**.
6. Fill in the build settings:
   - **Project name:** `herosbook` (or whatever you like — this becomes the URL, see below).
   - **Production branch:** `main`.
   - **Framework preset:** `None`.
   - **Build command:** `exit 0` (Cloudflare's documented value for "no build"; a blank field also works, but `exit 0` is what their static-HTML guide recommends).
   - **Build output directory:** `app`
   - **Root directory (advanced):** leave blank.
   - **Environment variables:** none.
7. Click **Save and Deploy**. The first "build" takes a minute or two even though it builds nothing — it is cloning the repo and uploading the files.

### Your URL

The site lives at `https://<project-name>.pages.dev`, e.g. `https://herosbook.pages.dev`. Because the repo is private and there is nothing secret in `app/` beyond what the export filter already allows, an unguessable-ish project name is all the privacy this needs. (A custom domain is possible later under the project's **Custom domains** tab, but is not required.)

Free tier, for reference: 500 builds per month, 20,000 files per site, 25 MiB per file, and unlimited requests/bandwidth for static assets. A site this size will never notice any of those limits.

### From then on

Every push to `main` triggers a new deploy automatically. Pushes to other branches create preview deployments at their own URLs, which is handy for trying things without touching the tablets' version.

## 2. Check the deploy

1. In **Workers & Pages > your project > Deployments**, wait for the latest deployment to say **Success**.
2. Open `https://<project-name>.pages.dev` in a desktop browser. The app should load with art and data, not a directory listing or a 404.
3. Spot-check the data file directly: `https://<project-name>.pages.dev/data/player_data.json` should return JSON. If it 404s, the build output directory is wrong (see Troubleshooting).
4. Optional: in desktop DevTools, **Application > Service Workers** should show `sw.js` activated, and **Application > Cache Storage** should show a cache named after the current `CACHE_VERSION` (e.g. `herosbook-v1`).

## 3. Install on a Fire tablet (Silk)

Do this once per tablet:

1. Open the **Silk** browser and go to `https://<project-name>.pages.dev`.
2. Let the page load fully once while online — this is when the service worker installs and caches everything for offline use.
3. Tap the **menu button** (three dots) and choose **Add to Home Screen** (on some Silk versions it is under **Add to** or shows as an "install" banner).
4. Accept the name and tap **Add**. An icon appears on the Fire home screen (it may land in a "Web Apps" style grouping depending on Fire OS version).
5. Open the app from the icon, pick that tablet's hero, then turn WiFi off and reopen it to confirm offline mode works before handing it over.

## 4. Every-deploy checklist

Run through this after every between-session update:

1. **If campaign data changed:** rerun the export so `app/data/player_data.json` is current:

   ```
   python tools/export_player_data.py
   ```

   (Skip if only app code/CSS changed.)
2. **Bump `CACHE_VERSION`** in `app/sw.js`. This is what makes tablets replace their cached copy — a deploy without a bump will look like nothing changed on the tablets. Just increment the number:

   ```js
   const CACHE_VERSION = 'herosbook-v2';  // was v1
   ```
3. **Commit and push to `main`.**
4. **Wait for the deploy.** Check **Deployments** in the Cloudflare dashboard, or just reload the `pages.dev` URL on a desktop browser and confirm the change is live.
5. **Update each tablet.** Open the app, press and hold the gear for about a second to enter the grown-up corner, and use **force an update check**. The new service worker installs the fresh cache and the old one is deleted. If a tablet was offline, it picks the update up the next time it does this while on WiFi.

## 5. Netlify alternative

Same idea, different buttons. Netlify's free tier (100 GB bandwidth, 300 build minutes per month) is also far more than this app needs, especially since there is no build to spend minutes on.

1. Sign up free at https://app.netlify.com/signup (using "Sign up with GitHub" is easiest).
2. **Add new project > Import an existing project > GitHub.** Authorize the Netlify GitHub app; when GitHub asks about repository access, grant it to `rpg_kids_companion` only. Private repos are fully supported.
3. Configure the project:
   - **Branch to deploy:** `main`
   - **Base directory:** leave blank
   - **Build command:** leave blank
   - **Publish directory:** `app`
4. Click **Deploy**. You get `https://<site-name>.netlify.app`; the random generated name can be changed under **Project configuration > Change site name**.
5. Everything else — the deploy check, the tablet install, the every-deploy checklist — is identical to the Cloudflare sections above. Deploys trigger on every push to `main` here too.

## 6. Troubleshooting

- **Tablets show old content after a deploy.** Almost always: `CACHE_VERSION` was not bumped in `app/sw.js`. The service worker serves from its cache and only rebuilds it when the version string changes. Bump it, push, redeploy, then force the update check from the grown-up corner.
- **App loads but is empty / heroes missing, or `/data/player_data.json` returns 404.** The publish directory is wrong. It must be `app` (Cloudflare: **Build output directory**; Netlify: **Publish directory**). If it is blank or `/`, the host serves the repo root and every app path is off by one directory. Fix it in the project's build settings and redeploy.
- **Cloudflare deploy fails at the build step.** Make sure the build command is `exit 0` (or blank) and the framework preset is `None`. There is nothing to build; any real command here will fail.
- **Deployed fine, desktop shows the new version, tablet does not update even after the update check.** Fully close the app on the tablet (swipe it away) and reopen it on WiFi, then try the update check again. A waiting service worker sometimes needs all app windows closed before it activates, though `skipWaiting` in `sw.js` makes this rare.
- **Add to Home Screen missing in Silk.** Make sure you are on the `https://` URL (not a local/`http://` address) and the page has fully loaded once. On older Silk versions the option can be buried under the share/menu icons; worst case, the site still works fine as a bookmarked page.
