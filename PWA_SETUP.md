# 📱 PWA (Progressive Web App) Setup Guide

## What's New?

PriorityIQ is now a **Progressive Web App**! Users can install it on their phones and use it like a native app with offline support.

## Features Added

✅ **Install on Mobile** - Add to home screen on iOS/Android  
✅ **Offline Support** - Access cached pages without internet  
✅ **App-like Experience** - Full-screen mode, no browser UI  
✅ **Fast Loading** - Service worker caching  
✅ **Push Notifications** - (Already implemented)  

## Setup Instructions

### 1. Install Pillow (for icon generation)
```bash
pip install Pillow
```

### 2. Generate App Icons
```bash
python ml/generate_icons.py
```

This creates:
- `static/icon-192.png` (192x192 icon)
- `static/icon-512.png` (512x512 icon)

### 3. Restart Flask
```bash
python app.py
```

## How Users Install the PWA

### On Android (Chrome/Edge)
1. Open PriorityIQ in Chrome
2. Click the "📱 Install App" button in the navigation bar
3. OR tap the menu (⋮) → "Add to Home screen"
4. Confirm installation
5. App appears on home screen!

### On iOS (Safari)
1. Open PriorityIQ in Safari
2. Tap the Share button (□↑)
3. Scroll down and tap "Add to Home Screen"
4. Name it "PriorityIQ" and tap "Add"
5. App appears on home screen!

### On Desktop (Chrome/Edge)
1. Open PriorityIQ in Chrome/Edge
2. Click the install icon (⊕) in the address bar
3. OR click "📱 Install App" button
4. Confirm installation
5. App opens in standalone window!

## Files Created

```
priorityIQ/
├── static/
│   ├── manifest.json          # PWA configuration
│   ├── service-worker.js      # Offline caching
│   ├── pwa.js                 # Install prompt logic
│   ├── icon-192.png          # App icon (small)
│   └── icon-512.png          # App icon (large)
└── ml/
    └── generate_icons.py      # Icon generator script
```

## PWA Capabilities

### Offline Mode
- Dashboard, tasks, and static assets are cached
- Users can view cached tasks without internet
- New data syncs when connection returns

### Standalone Mode
- Runs in full-screen without browser UI
- Looks and feels like a native app
- Custom splash screen with app icon

### Mobile Optimized
- Responsive viewport settings
- Touch-friendly interface
- Portrait orientation lock
- Status bar theming

## Testing PWA

### Check PWA Score
1. Open Chrome DevTools (F12)
2. Go to "Lighthouse" tab
3. Select "Progressive Web App"
4. Click "Generate report"
5. Aim for 90+ score!

### Test Offline Mode
1. Install the PWA
2. Open Chrome DevTools → Network tab
3. Check "Offline" checkbox
4. Reload the app
5. Dashboard should still load!

### Test Install Prompt
1. Open in Chrome (desktop/mobile)
2. Look for "📱 Install App" button
3. Click and confirm installation
4. App should open in standalone window

## Customization

### Change App Colors
Edit `static/manifest.json`:
```json
{
  "theme_color": "#4CAF50",        // Status bar color
  "background_color": "#ffffff"    // Splash screen color
}
```

### Add More Cached Pages
Edit `static/service-worker.js`:
```javascript
const urlsToCache = [
  '/',
  '/add',
  '/kanban',
  '/calendar',
  '/analytics'
];
```

### Update App Name
Edit `static/manifest.json`:
```json
{
  "name": "Your Custom Name",
  "short_name": "CustomApp"
}
```

## Benefits

🚀 **Faster Load Times** - Cached assets load instantly  
📱 **Mobile-First** - Optimized for touch devices  
🔒 **Secure** - HTTPS required for PWA features  
💾 **Offline Access** - Work without internet  
🏠 **Home Screen Icon** - Easy access like native apps  
🎨 **Branded Experience** - Custom colors and icons  

## Troubleshooting

### Install Button Not Showing
- Ensure you're using HTTPS (or localhost)
- Check browser supports PWA (Chrome, Edge, Safari)
- Clear cache and reload

### Service Worker Not Registering
- Check browser console for errors
- Verify `service-worker.js` is accessible at `/static/service-worker.js`
- Ensure no syntax errors in service worker

### Icons Not Loading
- Run `python ml/generate_icons.py` again
- Check `static/icon-192.png` and `static/icon-512.png` exist
- Clear browser cache

### Offline Mode Not Working
- Install the PWA first (service worker activates on install)
- Visit pages while online to cache them
- Check DevTools → Application → Service Workers

## Production Deployment

For production PWA deployment:

1. **Enable HTTPS** - PWA requires secure connection
2. **Update start_url** - Set to your production domain in `manifest.json`
3. **Add real icons** - Replace generated icons with professional designs
4. **Test on real devices** - iOS and Android behave differently
5. **Monitor cache size** - Don't cache too many large files

## Next Steps

- Add push notification support (already implemented!)
- Create custom splash screens
- Add app shortcuts in manifest
- Implement background sync for offline task creation
- Add share target API for sharing tasks

---

**Your app is now installable on any device! 🎉**
