# DriftDetector Web UI

Modern, interactive web dashboard for the DriftDetector ML anomaly detection system.

## Features

- ✨ **Real-time Predictions**: Submit sensor data and get instant anomaly predictions
- 📊 **Interactive Charts**: Visualize prediction history with Chart.js
- 💚 **Health Monitoring**: Real-time service status and uptime tracking
- 🔍 **Drift Detection**: Monitor data distribution changes
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile
- 🎨 **Modern UI**: Built with Tailwind CSS for beautiful aesthetics

## Quick Start

### Local Development

Simply open `index.html` in your browser:

```bash
cd ui
open index.html  # macOS
# or
start index.html  # Windows
# or
xdg-open index.html  # Linux
```

### Configuration

Edit `config.js` to point to your API endpoints:

```javascript
const API_CONFIG = {
    INFERENCE_API: 'http://4.187.158.249',
    DRIFT_API: 'http://4.187.158.249:8001'
};
```

## Deployment

### Azure Static Web Apps

1. **Create Static Web App**:
   ```bash
   az staticwebapp create \
     --name driftdetector-ui \
     --resource-group rg-pred-maint-prod \
     --source https://github.com/nishchalnishant/DriftDetector \
     --location "eastus" \
     --branch main \
     --app-location "/ui" \
     --api-location "" \
     --output-location ""
   ```

2. **Deploy**:
   - Push to GitHub
   - GitHub Actions automatically deploys
   - Access at: `https://driftdetector-ui.azurestaticapps.net`

### Using Local Server

For development with live reload:

```bash
# Using Python
python -m http.server 8080

# Using Node.js
npx serve .

# Access at http://localhost:8080
```

## API Endpoints Used

### Inference API (`http://4.187.158.249`)
- `GET /health` - Service health status
- `POST /predict` - Single prediction
- `GET /metrics` - Prometheus metrics

### Drift Detection API (`http://4.187.158.249:8001`)
- `GET /health` - Drift service status
- `GET /drift/latest` - Latest drift analysis
- `GET /metrics` - Drift metrics

## Tech Stack

- **HTML5** - Structure
- **Tailwind CSS** - Styling (via CDN)
- **Vanilla JavaScript** - Logic (no frameworks!)
- **Chart.js** - Data visualization
- **Font Awesome** - Icons

## Browser Support

- Chrome/Edge: ✅ Latest 2 versions
- Firefox: ✅ Latest 2 versions
- Safari: ✅ Latest 2 versions

## Screenshots

### Main Dashboard
- Service status cards
- Prediction form
- Real-time results
- History charts

### Features
- Responsive layout
- Dark mode ready
- Accessibility compliant
- Performance optimized

## Development

No build step required! Pure HTML/CSS/JS for simplicity.

### File Structure
```
ui/
├── index.html          # Main dashboard
├── app.js              # Application logic
├── config.js           # API configuration
├── staticwebapp.config.json  # Azure SWA config
└── README.md           # This file
```

## License

MIT License - See main repository for details

