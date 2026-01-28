// State management
const appState = {
    predictionHistory: [],
    anomalyCount: 0,
    predictionCount: 0,
    healthStatus: null,
    driftStatus: null
};

// Chart instance
let historyChart = null;

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    console.log('DriftDetector Dashboard Initialized');

    // Setup event listeners
    document.getElementById('predictionForm').addEventListener('submit', handlePrediction);

    // Initial health check
    await checkHealth();
    await checkDrift();

    // Setup periodic health checks
    setInterval(checkHealth, API_CONFIG.HEALTH_CHECK_INTERVAL);
    setInterval(checkDrift, API_CONFIG.DRIFT_CHECK_INTERVAL);

    // Initialize chart
    initializeChart();
});

// Health check function
async function checkHealth() {
    try {
        const response = await fetch(getEndpointURL('inference', 'HEALTH'));
        const data = await response.json();

        appState.healthStatus = data;
        updateHealthUI(data);

    } catch (error) {
        console.error('Health check failed:', error);
        updateHealthUI({ status: 'error', model_loaded: false, uptime_seconds: 0 });
    }
}

// Update health UI
function updateHealthUI(data) {
    const healthIndicator = document.getElementById('healthIndicator');
    const serviceStatus = document.getElementById('serviceStatus');
    const statusValue = document.getElementById('statusValue');
    const uptimeValue = document.getElementById('uptimeValue');

    // Update status badge
    if (data.status === 'healthy') {
        healthIndicator.innerHTML = `
            <span class="pulse-dot w-3 h-3 bg-green-400 rounded-full"></span>
            <span class="font-medium">Healthy</span>
        `;
        serviceStatus.className = 'text-xs font-semibold px-3 py-1 rounded-full bg-green-100 text-green-700';
        serviceStatus.textContent = 'Online';
    } else if (data.status === 'degraded') {
        healthIndicator.innerHTML = `
            <span class="pulse-dot w-3 h-3 bg-yellow-400 rounded-full"></span>
            <span class="font-medium">Degraded</span>
        `;
        serviceStatus.className = 'text-xs font-semibold px-3 py-1 rounded-full bg-yellow-100 text-yellow-700';
        serviceStatus.textContent = 'Degraded';
    } else {
        healthIndicator.innerHTML = `
            <span class="pulse-dot w-3 h-3 bg-red-400 rounded-full"></span>
            <span class="font-medium">Error</span>
        `;
        serviceStatus.className = 'text-xs font-semibold px-3 py-1 rounded-full bg-red-100 text-red-700';
        serviceStatus.textContent = 'Offline';
    }

    // Update status value
    statusValue.textContent = data.model_loaded ? 'Model Loaded' : 'No Model';

    // Update uptime
    const uptime = formatUptime(data.uptime_seconds || 0);
    uptimeValue.textContent = uptime;
}

// Format uptime
function formatUptime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (hours > 24) {
        const days = Math.floor(hours / 24);
        return `${days}d ${hours % 24}h`;
    }
    return `${hours}h ${minutes}m`;
}

// Check drift status
async function checkDrift() {
    try {
        const response = await fetch(getEndpointURL('drift', 'DRIFT_HEALTH'));
        const data = await response.json();

        appState.driftStatus = data;
        updateDriftUI(data);

    } catch (error) {
        console.error('Drift check failed:', error);
        updateDriftUI({ status: 'error' });
    }
}

// Update drift UI
function updateDriftUI(data) {
    document.getElementById('driftHealth').textContent = data.status || 'Unknown';
    document.getElementById('driftReference').textContent = data.reference_data_loaded ? 'Loaded' : 'Not Loaded';
    document.getElementById('driftThreshold').textContent = data.drift_threshold || 'N/A';
}

// Handle prediction
async function handlePrediction(e) {
    e.preventDefault();

    const button = document.getElementById('predictBtn');
    const originalText = button.innerHTML;

    // Show loading state
    button.disabled = true;
    button.innerHTML = '<span class="loading mr-2"></span> Predicting...';

    try {
        // Gather input data
        const inputData = {
            location: document.getElementById('location').value,
            temperature: parseFloat(document.getElementById('temperature').value),
            pressure: parseFloat(document.getElementById('pressure').value),
            humidity: parseFloat(document.getElementById('humidity').value),
            wind_speed: parseFloat(document.getElementById('windSpeed').value)
        };

        // Make prediction request
        const response = await fetch(getEndpointURL('inference', 'PREDICT'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(inputData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        // Update state
        appState.predictionCount++;

        // Track accuracy (updated from backend stats)
        const accuracyPercent = Math.round(result.forecast_accuracy * 100);
        document.getElementById('accuracyValue').textContent = `${accuracyPercent}%`;

        // Add to history (accuracy-based)
        appState.predictionHistory.push({
            timestamp: new Date(),
            score: result.forecast_accuracy,  // Use accuracy instead of anomaly score
            needsRetraining: result.needs_retraining,
            confidence: result.confidence
        });

        // Keep only last 20 predictions
        if (appState.predictionHistory.length > 20) {
            appState.predictionHistory.shift();
        }

        // Update UI
        updatePredictionCounts();
        displayResult(result, inputData);
        updateChart();

    } catch (error) {
        console.error('Prediction failed:', error);
        alert('Prediction failed: ' + error.message);
    } finally {
        // Reset button
        button.disabled = false;
        button.innerHTML = originalText;
    }
}

// Update prediction counts
function updatePredictionCounts() {
    document.getElementById('predictionCount').textContent = appState.predictionCount;
    document.getElementById('anomalyCount').textContent = appState.anomalyCount;
}

// Display prediction result
function displayResult(result, input) {
    const resultCard = document.getElementById('resultCard');
    const resultContent = document.getElementById('resultContent');

    const anomalyClass = result.is_anomaly ? 'anomaly-detected' : 'anomaly-normal';
    const anomalyIcon = result.is_anomaly ? 'fa-exclamation-triangle' : 'fa-check-circle';
    const anomalyColor = result.is_anomaly ? 'text-red-600' : 'text-green-600';
    const anomalyBg = result.is_anomaly ? 'bg-red-100' : 'bg-green-100';
    const anomalyText = result.is_anomaly ? 'ANOMALY DETECTED' : 'NORMAL OPERATION';

    resultContent.innerHTML = `
        <div class="anomaly-card ${anomalyClass} p-6 rounded-lg">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                    <div class="${anomalyBg} rounded-full p-3">
                        <i class="fas ${anomalyIcon} ${anomalyColor} text-2xl"></i>
                    </div>
                    <div>
                        <h3 class="text-lg font-bold ${anomalyColor}">${anomalyText}</h3>
                        <p class="text-sm text-gray-500">Location: ${result.location || input.location}</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-2xl font-bold ${anomalyColor}">${(result.confidence * 100).toFixed(1)}%</p>
                    <p class="text-xs text-gray-500">Confidence</p>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4 mb-4">
                <div class="bg-gray-50 p-3 rounded-lg">
                    <p class="text-xs text-gray-500">Anomaly Score</p>
                    <p class="text-lg font-bold text-gray-800">${result.anomaly_score.toFixed(4)}</p>
                </div>
                <div class="bg-gray-50 p-3 rounded-lg">
                    <p class="text-xs text-gray-500">Model Version</p>
                    <p class="text-lg font-bold text-gray-800">${result.model_version || 'v1'}</p>
                </div>
            </div>
            
            <div class="border-t pt-4">
                <p class="text-xs text-gray-500 mb-2">Weather Parameters</p>
                <div class="grid grid-cols-3 gap-2 text-xs">
                    <div><span class="text-gray-500">Temp:</span> <strong>${input.temperature}°C</strong></div>
                    <div><span class="text-gray-500">Pressure:</span> <strong>${input.pressure} hPa</strong></div>
                    <div><span class="text-gray-500">Humidity:</span> <strong>${input.humidity}%</strong></div>
                    <div><span class="text-gray-500">Wind Speed:</span> <strong>${input.wind_speed} m/s</strong></div>
                    <div><span class="text-gray-500">Location:</span> <strong>${input.location}</strong></div>
                    <div><span class="text-gray-500">Time:</span> <strong>${new Date().toLocaleTimeString()}</strong></div>
                </div>
            </div>
        </div>
    `;

    resultCard.classList.remove('hidden');
}

// Initialize chart
function initializeChart() {
    const ctx = document.getElementById('historyChart').getContext('2d');

    historyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Anomaly Score',
                data: [],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: function (context) {
                    const index = context.dataIndex;
                    return appState.predictionHistory[index]?.isAnomaly ? '#ef4444' : '#10b981';
                },
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const dataPoint = appState.predictionHistory[context.dataIndex];
                            return [
                                `Score: ${context.parsed.y.toFixed(4)}`,
                                `Confidence: ${(dataPoint.confidence * 100).toFixed(1)}%`,
                                `Status: ${dataPoint.isAnomaly ? 'Anomaly' : 'Normal'}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    title: {
                        display: true,
                        text: 'Anomaly Score'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Time'
                    }
                }
            }
        }
    });
}

// Update chart with new data
function updateChart() {
    if (!historyChart) return;

    historyChart.data.labels = appState.predictionHistory.map((p, i) =>
        p.timestamp.toLocaleTimeString()
    );

    historyChart.data.datasets[0].data = appState.predictionHistory.map(p => p.score);

    historyChart.update();
}
