document.addEventListener('DOMContentLoaded', () => {
    // --- Elements ---
    const startBtn = document.getElementById('start-btn');
    const nextLapBtn = document.getElementById('next-lap-btn');
    const lapCounter = document.getElementById('lap-counter');
    const racePhase = document.getElementById('race-phase');
    const hypeValue = document.getElementById('hype-value');
    const hypeFill = document.getElementById('hype-fill');
    const driverBody = document.getElementById('driver-body');
    const commentaryScroll = document.getElementById('commentary-scroll');
    const eventLog = document.getElementById('event-log');

    // --- State ---
    let chart = null;
    const maxChartPoints = 10;
    const chartData = {}; // driver -> array of gaps

    // --- initialization ---
    initChart();

    // --- Event Listeners ---
    startBtn.addEventListener('click', startRace);
    nextLapBtn.addEventListener('click', fetchNextLap);

    // --- Functions ---

    async function startRace() {
        const raceId = document.getElementById('raceSelector').value;
        resetDashboard();
        try {
            const response = await fetch('/api/race/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ race_id: raceId })
            });
            const data = await response.json();

            updateUI(data);
            startBtn.disabled = true;
            nextLapBtn.disabled = false;
        } catch (error) {
            console.error('Error starting race:', error);
            addCommentary("Error connecting to race server.");
        }
    }

    function resetDashboard() {
        // Reset labels
        lapCounter.textContent = "0/0";
        racePhase.textContent = "INITIALIZING";

        // Reset Hype
        hypeValue.textContent = "0";
        hypeFill.style.width = "0%";

        // Clear tables and feeds
        driverBody.innerHTML = '';
        commentaryScroll.innerHTML = '';
        eventLog.innerHTML = '';

        // Reset Chart
        chart.data.labels = [];
        chart.data.datasets = [];
        chart.update();
    }

    async function fetchNextLap() {
        try {
            const response = await fetch('/api/race/next-lap', { method: 'POST' });

            if (response.status === 204) {
                addCommentary("Chequered flag! The race simulation has concluded.");
                nextLapBtn.disabled = true;
                return;
            }

            const data = await response.json();
            updateUI(data);
        } catch (error) {
            console.error('Error fetching next lap:', error);
        }
    }

    function updateUI(data) {
        // 1. Header Info
        lapCounter.textContent = `${data.lap_number}/${data.total_laps}`;
        racePhase.textContent = data.race_phase.toUpperCase();

        // 2. Hype Index
        hypeValue.textContent = Math.round(data.hype_index);
        hypeFill.style.width = `${data.hype_index}%`;

        // Color coding hype value
        if (data.hype_index > 70) hypeValue.style.color = '#ff4d4d';
        else if (data.hype_index > 40) hypeValue.style.color = '#ffcc00';
        else hypeValue.style.color = '#00ff87';

        // 3. Driver Table
        updateDriverTable(data.drivers);

        // 4. Chart
        updateChart(data.drivers, data.lap_number);

        // 5. Commentary
        if (data.commentary) {
            addCommentary(data.commentary);
        }

        // 6. Event Log
        if (data.events && data.events.length > 0) {
            data.events.forEach(event => addEvent(event));
        }
    }

    function updateDriverTable(drivers) {
        driverBody.innerHTML = '';
        drivers.forEach(d => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${d.position}</td>
                <td class="driver-name">${d.driver}</td>
                <td>${d.lap_time.toFixed(3)}s</td>
                <td>${d.gap_ahead > 0 ? '+' + d.gap_ahead.toFixed(3) : 'LEAD'}</td>
                <td>${d.tire_compound}</td>
                <td style="color: ${d.tire_age > 20 ? '#ff4d4d' : 'inherit'}">${d.tire_age}</td>
            `;
            driverBody.appendChild(row);
        });
    }

    function addCommentary(text) {
        const item = document.createElement('div');
        item.className = 'commentary-item';
        item.innerHTML = `<p>${text}</p>`;
        commentaryScroll.prepend(item);
    }

    function addEvent(event) {
        const card = document.createElement('div');
        card.className = 'event-card';
        card.innerHTML = `
            <span class="event-type">${event.event_type}</span>
            <span class="event-drivers">${event.drivers_involved.join(' vs ')}</span>
        `;
        eventLog.prepend(card);
    }

    function initChart() {
        const ctx = document.getElementById('gap-chart').getContext('2d');
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        reverse: true,
                        title: { display: true, text: 'Gap to Lead (s)', color: '#949ca3' },
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#949ca3' }
                    },
                    x: {
                        title: { display: true, text: 'Lap', color: '#949ca3' },
                        grid: { display: false },
                        ticks: { color: '#949ca3' }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: '#ffffff', font: { size: 10 } }
                    }
                },
                animation: { duration: 400 }
            }
        });
    }

    function updateChart(drivers, lap) {
        if (!chart.data.labels.includes(lap)) {
            chart.data.labels.push(lap);
            if (chart.data.labels.length > maxChartPoints) chart.data.labels.shift();
        }

        drivers.slice(0, 5).forEach((d, idx) => {
            let dataset = chart.data.datasets.find(ds => ds.label === d.driver);
            if (!dataset) {
                const colors = ['#e10600', '#00d2ff', '#00ff87', '#ffcc00', '#ffffff'];
                dataset = {
                    label: d.driver,
                    data: [],
                    borderColor: colors[idx % colors.length],
                    tension: 0.3,
                    borderWidth: 2,
                    pointRadius: 0
                };
                chart.data.datasets.push(dataset);
            }

            dataset.data.push(d.gap_ahead);
            if (dataset.data.length > maxChartPoints) dataset.data.shift();
        });

        chart.update();
    }
});
