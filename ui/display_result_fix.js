// Display prediction result
function displayResult(result, input) {
    const resultCard = document.getElementById('resultCard');
    const resultContent = document.getElementById('resultContent');

    const accuracyPercent = (result.forecast_accuracy * 100).toFixed(1);
    const isAccurate = result.forecast_accuracy >= 0.7;
    const statusClass = isAccurate ? 'anomaly-normal' : 'anomaly-detected';
    const statusIcon = isAccurate ? 'fa-check-circle' : 'fa-exclamation-triangle';
    const statusColor = isAccurate ? 'text-green-600' : 'text-orange-600';
    const statusBg = isAccurate ? 'bg-green-100' : 'bg-orange-100';
    const statusText = isAccurate ? 'HIGH ACCURACY' : 'NEEDS RETRAINING';

    resultContent.innerHTML = `
        <div class="anomaly-card ${statusClass} p-6 rounded-lg">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                    <div class="${statusBg} rounded-full p-3">
                        <i class="fas ${statusIcon} ${statusColor} text-2xl"></i>
                    </div>
                    <div>
                        <h3 class="text-lg font-bold ${statusColor}">${statusText}</h3>
                        <p class="text-sm text-gray-500">📍 ${result.location || input.location}</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-2xl font-bold ${statusColor}">${accuracyPercent}%</p>
                    <p class="text-xs text-gray-500">Forecast Accuracy</p>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4 mb-4">
                <div class="bg-gray-50 p-3 rounded-lg">
                    <p class="text-xs text-gray-500">Confidence</p>
                    <p class="text-lg font-bold text-gray-800">${(result.confidence * 100).toFixed(1)}%</p>
                </div>
                <div class="bg-gray-50 p-3 rounded-lg">
                    <p class="text-xs text-gray-500">Model Version</p>
                    <p class="text-lg font-bold text-gray-800">${result.model_version || 'v1.0.0'}</p>
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
