/* ── Progresif Vedik Astroloji — Chart Renderer ─────────────── */

// ── Constants ───────────────────────────────────────────────────

const SIGN_ABBR = [
    'Ar', 'Ta', 'Ge', 'Ca', 'Le', 'Vi',
    'Li', 'Sc', 'Sg', 'Cp', 'Aq', 'Pi'
];

const SIGN_NAMES_TR = [
    'Koç', 'Boğa', 'İkizler', 'Yengeç', 'Aslan', 'Başak',
    'Terazi', 'Akrep', 'Yay', 'Oğlak', 'Kova', 'Balık'
];

// South Indian chart: sign index → grid position [row, col]
const SIGN_GRID = {
    11: [0, 0],  0: [0, 1],  1: [0, 2],  2: [0, 3],
    10: [1, 0],                            3: [1, 3],
     9: [2, 0],                            4: [2, 3],
     8: [3, 0],  7: [3, 1],  6: [3, 2],  5: [3, 3]
};

const PLANET_COLORS = {
    'Su': '#f0a030', 'Mo': '#c0c8d8', 'Ma': '#e05040',
    'Me': '#50b860', 'Ju': '#e8b030', 'Ve': '#d870b8',
    'Sa': '#5888c8', 'Ra': '#808890', 'Ke': '#808890'
};


// ── SVG South Indian Chart ──────────────────────────────────────

function createSVGElement(tag, attrs) {
    const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [k, v] of Object.entries(attrs)) {
        el.setAttribute(k, v);
    }
    return el;
}

function drawSouthIndianChart(containerId, planets, lagnaSignIndex, title) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    const W = 440, H = 440;
    const margin = 20;
    const cellW = (W - 2 * margin) / 4;
    const cellH = (H - 2 * margin) / 4;

    const svg = createSVGElement('svg', {
        width: W, height: H, viewBox: `0 0 ${W} ${H}`
    });

    // Background
    svg.appendChild(createSVGElement('rect', {
        x: 0, y: 0, width: W, height: H,
        fill: '#161b22', rx: 8
    }));

    // Group planets by sign index
    const planetsBySign = {};
    for (let i = 0; i < 12; i++) planetsBySign[i] = [];
    for (const p of planets) {
        const signIdx = p.sign_index;
        if (planetsBySign[signIdx]) {
            planetsBySign[signIdx].push(p);
        }
    }

    // Draw cells
    for (let signIdx = 0; signIdx < 12; signIdx++) {
        const pos = SIGN_GRID[signIdx];
        if (!pos) continue;

        const x = margin + pos[1] * cellW;
        const y = margin + pos[0] * cellH;

        const isLagna = signIdx === lagnaSignIndex;

        // Cell background
        svg.appendChild(createSVGElement('rect', {
            x: x, y: y, width: cellW, height: cellH,
            fill: isLagna ? 'rgba(201,162,39,0.08)' : 'transparent',
            stroke: '#30363d',
            'stroke-width': 1
        }));

        // Sign label (top-left)
        const signLabel = createSVGElement('text', {
            x: x + 5, y: y + 14,
            'font-size': '10', fill: '#484f58',
            'font-family': 'sans-serif'
        });
        signLabel.textContent = SIGN_NAMES_TR[signIdx];
        svg.appendChild(signLabel);

        // House number (top-right)
        const houseNum = ((signIdx - lagnaSignIndex + 12) % 12) + 1;
        const houseLabel = createSVGElement('text', {
            x: x + cellW - 5, y: y + 14,
            'font-size': '10', fill: '#484f58',
            'font-family': 'sans-serif',
            'text-anchor': 'end'
        });
        houseLabel.textContent = houseNum;
        svg.appendChild(houseLabel);

        // Lagna marker (diagonal line in corner)
        if (isLagna) {
            svg.appendChild(createSVGElement('line', {
                x1: x, y1: y + 18,
                x2: x + 18, y2: y,
                stroke: '#c9a227',
                'stroke-width': 2
            }));
        }

        // Planets in this sign
        const cellPlanets = planetsBySign[signIdx];
        if (cellPlanets.length > 0) {
            const startY = y + 30;
            const availableH = cellH - 35;
            const lineH = Math.min(16, availableH / cellPlanets.length);

            for (let i = 0; i < cellPlanets.length; i++) {
                const p = cellPlanets[i];
                const py = startY + i * lineH;
                const color = PLANET_COLORS[p.abbr] || '#e6edf3';

                let label = p.abbr;
                if (p.retrograde) label += '(R)';

                const text = createSVGElement('text', {
                    x: x + cellW / 2,
                    y: py + 10,
                    'font-size': '13',
                    'font-weight': '600',
                    fill: color,
                    'text-anchor': 'middle',
                    'font-family': 'sans-serif'
                });
                text.textContent = label;
                svg.appendChild(text);
            }
        }
    }

    // Center area — chart label
    const cx = margin + cellW;
    const cy = margin + cellH;
    const cw = cellW * 2;
    const ch = cellH * 2;

    svg.appendChild(createSVGElement('rect', {
        x: cx, y: cy, width: cw, height: ch,
        fill: '#0d1117',
        stroke: '#30363d',
        'stroke-width': 1
    }));

    const titleText = createSVGElement('text', {
        x: cx + cw / 2, y: cy + ch / 2 - 8,
        'font-size': '16', 'font-weight': '700',
        fill: '#c9a227',
        'text-anchor': 'middle',
        'font-family': 'sans-serif'
    });
    titleText.textContent = title || 'D1 Rasi';
    svg.appendChild(titleText);

    const lagnaText = createSVGElement('text', {
        x: cx + cw / 2, y: cy + ch / 2 + 14,
        'font-size': '12',
        fill: '#8b949e',
        'text-anchor': 'middle',
        'font-family': 'sans-serif'
    });
    lagnaText.textContent = 'Lagna: ' + SIGN_NAMES_TR[lagnaSignIndex];
    svg.appendChild(lagnaText);

    container.appendChild(svg);
}


// ── Render Results ──────────────────────────────────────────────

function renderResults(data) {
    document.getElementById('results').style.display = 'block';

    renderSummary(data);
    renderD1Chart(data);
    renderD9Chart(data);
    renderPlanetsTable(data);
    renderNakshatraTable(data);
    renderNavamshaTable(data);
    renderDashaTable(data);

    // Scroll to results
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
}

function renderSummary(data) {
    const bi = data.birth_info;
    const l = data.lagna;
    const nak = l.nakshatra;

    const html = `
        <div class="summary-item">
            <div class="label">Doğum</div>
            <div class="value">${bi.date} — ${bi.time}</div>
        </div>
        <div class="summary-item">
            <div class="label">Saat Dilimi</div>
            <div class="value">${bi.timezone}</div>
        </div>
        <div class="summary-item">
            <div class="label">Koordinatlar</div>
            <div class="value">${bi.latitude.toFixed(4)}°N, ${bi.longitude_geo.toFixed(4)}°E</div>
        </div>
        <div class="summary-item">
            <div class="label">Ayanamsa</div>
            <div class="value">${data.ayanamsa.type} (${data.ayanamsa.value}°)</div>
        </div>
        <div class="summary-item">
            <div class="label">Lagna (Ascendant)</div>
            <div class="value gold">${l.sign} — ${l.degree_str}</div>
        </div>
        <div class="summary-item">
            <div class="label">Lagna Nakshatra</div>
            <div class="value">${nak.name} Pada ${nak.pada} (${nak.lord})</div>
        </div>
    `;
    document.getElementById('summary-content').innerHTML = html;
}

function renderD1Chart(data) {
    const planets = data.planets.map(p => ({
        abbr: p.abbr,
        sign_index: p.sign_index,
        retrograde: p.retrograde
    }));
    // Add Lagna marker as "Asc"
    planets.push({
        abbr: 'Asc',
        sign_index: data.lagna.sign_index,
        retrograde: false
    });

    drawSouthIndianChart('d1-chart', planets, data.lagna.sign_index, 'D1 Rasi');
}

function renderD9Chart(data) {
    const planets = data.planets.map(p => ({
        abbr: p.abbr,
        sign_index: p.navamsha_sign_index,
        retrograde: p.retrograde
    }));
    // Navamsha Lagna
    planets.push({
        abbr: 'Asc',
        sign_index: data.navamsha_lagna.sign_index,
        retrograde: false
    });

    drawSouthIndianChart('d9-chart', planets, data.navamsha_lagna.sign_index, 'D9 Navamsha');
}

function renderPlanetsTable(data) {
    const tbody = document.querySelector('#planets-table tbody');
    let rows = '';
    for (const p of data.planets) {
        const retro = p.retrograde
            ? '<span class="retro-badge">R</span>'
            : '';
        rows += `<tr>
            <td class="planet-${p.abbr}" style="font-weight:600">${p.name}</td>
            <td>${p.sign}</td>
            <td>${p.degree_str}</td>
            <td>${p.house}</td>
            <td>${retro}</td>
        </tr>`;
    }
    tbody.innerHTML = rows;
}

function renderNakshatraTable(data) {
    const tbody = document.querySelector('#nakshatra-table tbody');
    let rows = '';
    for (const p of data.planets) {
        const n = p.nakshatra;
        rows += `<tr>
            <td class="planet-${p.abbr}" style="font-weight:600">${p.name}</td>
            <td>${n.name}</td>
            <td>${n.pada}</td>
            <td>${n.lord}</td>
        </tr>`;
    }
    tbody.innerHTML = rows;
}

function renderNavamshaTable(data) {
    const tbody = document.querySelector('#navamsha-table tbody');
    let rows = `<tr>
        <td style="font-weight:600;color:#c9a227">Lagna (D9)</td>
        <td>${data.navamsha_lagna.sign}</td>
        <td>${data.navamsha_lagna.degree_str}</td>
    </tr>`;
    for (const p of data.planets) {
        rows += `<tr>
            <td class="planet-${p.abbr}" style="font-weight:600">${p.name}</td>
            <td>${p.navamsha_sign}</td>
            <td>${p.navamsha_degree_str}</td>
        </tr>`;
    }
    tbody.innerHTML = rows;
}

function renderDashaTable(data) {
    const tbody = document.querySelector('#dasha-table tbody');
    let rows = '';
    for (const d of data.vimshottari_dasha) {
        const badge = d.is_birth_dasha
            ? '<span class="birth-badge">doğum</span>'
            : '';
        rows += `<tr>
            <td style="font-weight:600">${d.lord}</td>
            <td>${d.effective_years}</td>
            <td>${d.start}</td>
            <td>${d.end}</td>
            <td>${badge}</td>
        </tr>`;
    }
    tbody.innerHTML = rows;
}


// ── Form Handling ───────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('chart-form');
    const citySelect = document.getElementById('city-select');
    const errorBox = document.getElementById('error-box');
    const btnCalculate = document.getElementById('btn-calculate');
    const btnText = btnCalculate.querySelector('.btn-text');
    const btnLoading = btnCalculate.querySelector('.btn-loading');

    // City select → auto-fill coordinates & timezone
    citySelect.addEventListener('change', function() {
        const val = this.value;
        if (!val) return;
        const parts = val.split(',');
        document.getElementById('lat').value = parts[0];
        document.getElementById('lon').value = parts[1];
        document.getElementById('tz_offset').value = parts[2];
    });

    // Form submit
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        errorBox.style.display = 'none';

        const payload = {
            year: document.getElementById('year').value,
            month: document.getElementById('month').value,
            day: document.getElementById('day').value,
            hour: document.getElementById('hour').value,
            minute: document.getElementById('minute').value,
            tz_offset: document.getElementById('tz_offset').value,
            lat: document.getElementById('lat').value,
            lon: document.getElementById('lon').value,
        };

        // Disable button
        btnCalculate.disabled = true;
        btnText.style.display = 'none';
        btnLoading.style.display = 'inline';

        try {
            const resp = await fetch('/api/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await resp.json();

            if (!resp.ok) {
                throw new Error(data.error || 'Bilinmeyen hata');
            }

            renderResults(data);

        } catch (err) {
            errorBox.textContent = err.message;
            errorBox.style.display = 'block';
            document.getElementById('results').style.display = 'none';
        } finally {
            btnCalculate.disabled = false;
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
        }
    });
});
