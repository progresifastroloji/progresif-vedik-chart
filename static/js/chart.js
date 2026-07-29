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

const DASHAS_UNTIL_YEAR = 2050;
const DASHA_CHILD_KEY = {
    maha: 'antara',
    antara: 'pratyantar',
    pratyantar: 'sookshma'
};

const DASHA_LEVEL_LABEL = {
    maha: 'Maha',
    antara: 'Antar',
    pratyantar: 'Pratyantar',
    sookshma: 'Sookshma'
};

const VARGA_DIVISIONS = [
    'D1', 'D2', 'D3', 'D4', 'D6', 'D7', 'D9',
    'D10', 'D11', 'D12', 'D20', 'D24', 'D30', 'D60'
];
const VARGA_TITLES = {
    D1: 'D1 Rasi',
    D2: 'D2 Hora',
    D3: 'D3 Drekkana',
    D4: 'D4 Chaturthamsha',
    D6: 'D6 Shashthamsa',
    D7: 'D7 Saptamsha',
    D9: 'D9 Navamsha',
    D10: 'D10 Dashamsha',
    D11: 'D11 Rudramsa',
    D12: 'D12 Dwadashamsha',
    D20: 'D20 Vimshamsha',
    D24: 'D24 Chaturvimshamsha',
    D30: 'D30 Trimshamsha',
    D60: 'D60 Shashtiamsha'
};
const SPECIAL_LAGNA_ORDER = [
    'chandra_lagna',
    'surya_lagna',
    'hora_lagna',
    'ghati_lagna',
    'bhava_lagna',
    'indu_lagna'
];
const RECENT_SAVES_KEY = 'progresif_recent_vault_saves';
const RECTIFICATION_EVENTS_KEY = 'progresif_rectification_events_by_person';
const RECTIFICATION_API_BASE = 'http://127.0.0.1:5051';
const TURKEY_TIMEZONE_ID = 'Europe/Istanbul';
const TURKEY_OPTGROUP_LABEL = 'Türkiye';
const TURKEY_LAT_RANGE = [35, 43];
const TURKEY_LON_RANGE = [25, 45];
const TURKEY_BIRTH_PLACES = [
    { plate: '01', name: 'Adana', lat: '37.0000', lon: '35.3213' },
    { plate: '02', name: 'Adıyaman', lat: '37.7648', lon: '38.2786' },
    { plate: '03', name: 'Afyonkarahisar', lat: '38.7569', lon: '30.5387' },
    { plate: '04', name: 'Ağrı', lat: '39.7191', lon: '43.0503' },
    { plate: '05', name: 'Amasya', lat: '40.6499', lon: '35.8353' },
    { plate: '06', name: 'Ankara', lat: '39.9334', lon: '32.8597' },
    { plate: '07', name: 'Antalya', lat: '36.8969', lon: '30.7133' },
    { plate: '08', name: 'Artvin', lat: '41.1828', lon: '41.8183' },
    { plate: '09', name: 'Aydın', lat: '37.8450', lon: '27.8396' },
    { plate: '10', name: 'Balıkesir', lat: '39.6484', lon: '27.8826' },
    { plate: '11', name: 'Bilecik', lat: '40.1426', lon: '29.9793' },
    { plate: '12', name: 'Bingöl', lat: '38.8847', lon: '40.4939' },
    { plate: '13', name: 'Bitlis', lat: '38.4006', lon: '42.1095' },
    { plate: '14', name: 'Bolu', lat: '40.7350', lon: '31.6061' },
    { plate: '15', name: 'Burdur', lat: '37.7203', lon: '30.2908' },
    { plate: '16', name: 'Bursa', lat: '40.1885', lon: '29.0610' },
    { plate: '17', name: 'Çanakkale', lat: '40.1553', lon: '26.4142' },
    { plate: '18', name: 'Çankırı', lat: '40.6013', lon: '33.6134' },
    { plate: '19', name: 'Çorum', lat: '40.5506', lon: '34.9556' },
    { plate: '20', name: 'Denizli', lat: '37.7765', lon: '29.0864' },
    { plate: '21', name: 'Diyarbakır', lat: '37.9144', lon: '40.2306' },
    { plate: '22', name: 'Edirne', lat: '41.6771', lon: '26.5557' },
    { plate: '23', name: 'Elazığ', lat: '38.6748', lon: '39.2225' },
    { plate: '24', name: 'Erzincan', lat: '39.7468', lon: '39.4911' },
    { plate: '25', name: 'Erzurum', lat: '39.9043', lon: '41.2679' },
    { plate: '26', name: 'Eskişehir', lat: '39.7767', lon: '30.5206' },
    { plate: '27', name: 'Gaziantep', lat: '37.0662', lon: '37.3833' },
    { plate: '28', name: 'Giresun', lat: '40.9128', lon: '38.3895' },
    { plate: '29', name: 'Gümüşhane', lat: '40.4603', lon: '39.4814' },
    { plate: '30', name: 'Hakkari', lat: '37.5744', lon: '43.7408' },
    { plate: '31', name: 'Hatay', lat: '36.2023', lon: '36.1613' },
    { plate: '32', name: 'Isparta', lat: '37.7648', lon: '30.5566' },
    { plate: '33', name: 'Mersin', lat: '36.8121', lon: '34.6415' },
    { plate: '34', name: 'İstanbul', lat: '41.0082', lon: '28.9784' },
    { plate: '35', name: 'İzmir', lat: '38.4237', lon: '27.1428' },
    { plate: '36', name: 'Kars', lat: '40.6013', lon: '43.0975' },
    { plate: '37', name: 'Kastamonu', lat: '41.3887', lon: '33.7827' },
    { plate: '38', name: 'Kayseri', lat: '38.7205', lon: '35.4826' },
    { plate: '39', name: 'Kırklareli', lat: '41.7351', lon: '27.2252' },
    { plate: '40', name: 'Kırşehir', lat: '39.1458', lon: '34.1601' },
    { plate: '41', name: 'Kocaeli', lat: '40.7667', lon: '29.9167' },
    { plate: '42', name: 'Konya', lat: '37.8746', lon: '32.4932' },
    { plate: '43', name: 'Kütahya', lat: '39.4192', lon: '29.9857' },
    { plate: '44', name: 'Malatya', lat: '38.3552', lon: '38.3095' },
    { plate: '45', name: 'Manisa', lat: '38.6191', lon: '27.4289' },
    { plate: '46', name: 'Kahramanmaraş', lat: '37.5753', lon: '36.9228' },
    { plate: '47', name: 'Mardin', lat: '37.3212', lon: '40.7245' },
    { plate: '48', name: 'Muğla', lat: '37.2153', lon: '28.3636' },
    { plate: '49', name: 'Muş', lat: '38.7433', lon: '41.5065' },
    { plate: '50', name: 'Nevşehir', lat: '38.6244', lon: '34.7239' },
    { plate: '51', name: 'Niğde', lat: '37.9667', lon: '34.6833' },
    { plate: '52', name: 'Ordu', lat: '40.9847', lon: '37.8789' },
    { plate: '53', name: 'Rize', lat: '41.0201', lon: '40.5234' },
    { plate: '54', name: 'Sakarya', lat: '40.7731', lon: '30.3948' },
    { plate: '55', name: 'Samsun', lat: '41.2867', lon: '36.3300' },
    { plate: '56', name: 'Siirt', lat: '37.9333', lon: '41.9500' },
    { plate: '57', name: 'Sinop', lat: '42.0231', lon: '35.1531' },
    { plate: '58', name: 'Sivas', lat: '39.7477', lon: '37.0179' },
    { plate: '59', name: 'Tekirdağ', lat: '40.9780', lon: '27.5110' },
    { plate: '60', name: 'Tokat', lat: '40.3167', lon: '36.5500' },
    { plate: '61', name: 'Trabzon', lat: '41.0027', lon: '39.7168' },
    { plate: '62', name: 'Tunceli', lat: '39.1083', lon: '39.5483' },
    { plate: '63', name: 'Şanlıurfa', lat: '37.1591', lon: '38.7969' },
    { plate: '64', name: 'Uşak', lat: '38.6823', lon: '29.4082' },
    { plate: '65', name: 'Van', lat: '38.4942', lon: '43.3800' },
    { plate: '66', name: 'Yozgat', lat: '39.8181', lon: '34.8147' },
    { plate: '67', name: 'Zonguldak', lat: '41.4564', lon: '31.7987' },
    { plate: '68', name: 'Aksaray', lat: '38.3687', lon: '34.0370' },
    { plate: '69', name: 'Bayburt', lat: '40.2552', lon: '40.2249' },
    { plate: '70', name: 'Karaman', lat: '37.1811', lon: '33.2150' },
    { plate: '71', name: 'Kırıkkale', lat: '39.8468', lon: '33.5153' },
    { plate: '72', name: 'Batman', lat: '37.8812', lon: '41.1351' },
    { plate: '73', name: 'Şırnak', lat: '37.5164', lon: '42.4611' },
    { plate: '74', name: 'Bartın', lat: '41.6344', lon: '32.3375' },
    { plate: '75', name: 'Ardahan', lat: '41.1105', lon: '42.7022' },
    { plate: '76', name: 'Iğdır', lat: '39.9237', lon: '44.0450' },
    { plate: '77', name: 'Yalova', lat: '40.6500', lon: '29.2667' },
    { plate: '78', name: 'Karabük', lat: '41.2061', lon: '32.6204' },
    { plate: '79', name: 'Kilis', lat: '36.7184', lon: '37.1212' },
    { plate: '80', name: 'Osmaniye', lat: '37.0742', lon: '36.2478' },
    { plate: '81', name: 'Düzce', lat: '40.8438', lon: '31.1565' },
];

let lastChartData = null;
let lastPersonInfo = null;
let activeRectificationRecord = null;
let lastRectificationDecision = null;
let activeVargaDivision = 'D7';
let visibleRecentSaves = [];
let expertCopyRenderRequestId = 0;

const ANALYSIS_MODE_PROFILES = {
    client: {
        mode: 'client',
        label: 'Danışan modu',
        interpretation_language: 'soft_guidance',
        certainty_policy: 'olasılık ve eğilim dili; kesin hüküm yok',
        usage_rule: 'Danışana uygun sade dil kullan; güçlü göstergeleri bile olasılık/aktivasyon olarak ifade et.',
    },
    astrolog: {
        mode: 'astrolog',
        label: 'Astrolog modu',
        interpretation_language: 'strong_professional',
        certainty_policy: 'çoklu gösterge desteği varsa güçlü hüküm dili; yine de kader kesinliği yok',
        usage_rule: 'Natal vaat, dasha, transit ve varga aynı temayı destekliyorsa daha net astrolog dili kullan.',
    },
    technical: {
        mode: 'technical',
        label: 'Teknik mod',
        interpretation_language: 'evidence_first',
        certainty_policy: 'yorumdan önce veri, kural, güven ve eksik kontrol bildir',
        usage_rule: 'Yorum üretmeden önce teknik kanıtları, kullanılan kaynak alanlarını ve eksikleri açıkça sırala.',
    },
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
    activateTab('basic');

    renderSummary(data);
    renderDataQuality(data);
    renderD1Chart(data);
    renderD9Chart(data);
    renderVargaPanel(data, activeVargaDivision);
    renderPlanetsTable(data);
    renderNakshatraTable(data);
    renderNavamshaTable(data);
    renderAspectsTable(data);
    renderDashaTable(data);
    renderYogas(data);
    renderSpecialLagnas(data);
    renderAdvancedLayers(data);
    renderExpertCopyPackage(data);

    // Scroll to results
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
}

function activateTab(tabName) {
    const buttons = document.querySelectorAll('.tab-button');
    const panels = document.querySelectorAll('.tab-panel');

    buttons.forEach(button => {
        const isActive = button.dataset.tab === tabName;
        button.classList.toggle('active', isActive);
        button.setAttribute('aria-selected', String(isActive));
    });

    panels.forEach(panel => {
        const isActive = panel.dataset.panel === tabName;
        panel.classList.toggle('active', isActive);
        panel.hidden = !isActive;
    });
}

function bindResultTabs() {
    const tabs = document.querySelectorAll('.tab-button');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => activateTab(tab.dataset.tab));
    });
}

function openRectificationPanel() {
    const results = document.getElementById('results');
    const panel = document.getElementById('panel-rectification');
    if (results) {
        results.style.display = 'block';
    }
    activateTab('rectification');
    if (panel) {
        panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function bindVargaTabs() {
    const tabs = document.querySelectorAll('.varga-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            activeVargaDivision = tab.dataset.varga;
            if (lastChartData) {
                renderVargaPanel(lastChartData, activeVargaDivision);
            }
        });
    });
}

function getPersonInfo() {
    const name = document.getElementById('person-name').value.trim();
    const group = document.getElementById('group-name').value.trim() || 'Grup-01';
    return { name, group };
}

function selectedTransitRange() {
    const startDate = document.getElementById('transit-start-date').value;
    const endDate = document.getElementById('transit-end-date').value;
    if (!startDate && !endDate) return null;
    if (!startDate || !endDate) {
        throw new Error('Transit başlangıç ve bitiş tarihlerini birlikte seç.');
    }

    const start = Date.parse(`${startDate}T00:00:00Z`);
    const end = Date.parse(`${endDate}T00:00:00Z`);
    const dayCount = Math.round((end - start) / 86400000) + 1;
    if (dayCount < 1) {
        throw new Error('Transit bitiş tarihi başlangıç tarihinden önce olamaz.');
    }
    if (dayCount > 190) {
        throw new Error('Transit aralığı en fazla 190 gün olabilir.');
    }
    return { start_date: startDate, end_date: endDate, day_count: dayCount };
}

function rectificationPersonKey(person = getPersonInfo()) {
    if (!person.name) return null;
    return `${person.group || 'Grup-01'}::${person.name}`;
}

function loadRectificationEventStore() {
    try {
        const raw = localStorage.getItem(RECTIFICATION_EVENTS_KEY);
        const parsed = raw ? JSON.parse(raw) : {};
        return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {};
    } catch (err) {
        return {};
    }
}

function persistRectificationEventStore(store) {
    try {
        localStorage.setItem(RECTIFICATION_EVENTS_KEY, JSON.stringify(store));
    } catch (err) {
        // Local storage can be unavailable in private or restricted browser modes.
    }
}

function loadSavedRectificationEvents(person = getPersonInfo()) {
    const key = rectificationPersonKey(person);
    if (!key) return [];
    const store = loadRectificationEventStore();
    return Array.isArray(store[key]) ? store[key] : [];
}

function setVaultStatus(message, type) {
    const status = document.getElementById('vault-status');
    status.textContent = message || '';
    status.classList.toggle('success', type === 'success');
    status.classList.toggle('error', type === 'error');
}

function renderVaultSaveResult(result) {
    const status = document.getElementById('vault-status');
    const transit = result.transit || {};
    const transitThreeMonth = result.transit_3_month || {};
    const transitRange = result.transit_range || {};
    const savedParts = ['kişi dosyası'];
    if (transit.ok) savedParts.push('aylık transit');
    if (transitThreeMonth.ok) savedParts.push('3 aylık transit');
    if (transitRange.ok) {
        const period = transitRange.period || {};
        savedParts.push(`transit aralığı ${period.range_start || ''}–${period.range_end || ''}`);
    }

    status.classList.add('success');
    status.classList.remove('error');
    status.textContent = `Kaydedildi: ${savedParts.join(', ')}.`;
}

function loadRecentSaves() {
    try {
        const raw = localStorage.getItem(RECENT_SAVES_KEY);
        const parsed = raw ? JSON.parse(raw) : [];
        return Array.isArray(parsed) ? parsed : [];
    } catch (err) {
        return [];
    }
}

function persistRecentSaves(items) {
    try {
        localStorage.setItem(RECENT_SAVES_KEY, JSON.stringify(items));
    } catch (err) {
        // Local storage can be unavailable in private or restricted browser modes.
    }
}

function recentSaveKey(item) {
    return (
        item.paths &&
        (item.paths.person || item.paths.natal || item.paths.legacy_natal || item.paths.rectification)
    ) || `${item.group || 'Grup-01'}/${item.name || ''}`;
}

function sameRecentPerson(left, right) {
    const leftName = String((left && left.name) || '').trim().toLocaleLowerCase('tr-TR');
    const rightName = String((right && right.name) || '').trim().toLocaleLowerCase('tr-TR');
    const leftGroup = String((left && left.group) || 'Grup-01').trim().toLocaleLowerCase('tr-TR');
    const rightGroup = String((right && right.group) || 'Grup-01').trim().toLocaleLowerCase('tr-TR');
    return Boolean(leftName && rightName && leftName === rightName && leftGroup === rightGroup);
}

function recentPersonKey(item) {
    const name = String((item && item.name) || '').trim().toLocaleLowerCase('tr-TR');
    const group = String((item && item.group) || 'Grup-01').trim().toLocaleLowerCase('tr-TR');
    return name ? `${group}/${name}` : '';
}

function upsertRecentSaveItem(item) {
    const key = recentSaveKey(item);
    const items = loadRecentSaves()
        .filter(existing => recentSaveKey(existing) !== key && !sameRecentPerson(existing, item));
    items.unshift(item);
    persistRecentSaves(items);
    return items;
}

function mergeRecentAndVaultSaves(localItems, vaultItems) {
    const seenKeys = new Set();
    const seenPeople = new Map();
    const merged = [];

    [...localItems, ...vaultItems].forEach(item => {
        const key = recentSaveKey(item);
        const personKey = recentPersonKey(item);
        const existingPersonIndex = personKey ? seenPeople.get(personKey) : undefined;

        if (existingPersonIndex !== undefined) {
            const existing = merged[existingPersonIndex];
            if (item.source === 'vault') {
                merged[existingPersonIndex] = item;
                seenKeys.add(key);
            } else if (
                existing.source_type === 'rectification_events'
                && item.source_type !== 'rectification_events'
            ) {
                merged[existingPersonIndex] = item;
                seenKeys.add(key);
            }
            return;
        }

        if (seenKeys.has(key)) return;
        seenKeys.add(key);
        if (personKey) {
            seenPeople.set(personKey, merged.length);
        }
        merged.push(item);
    });

    return merged;
}

async function loadVaultSaveItems() {
    const response = await fetch('/api/v2/vault/list');
    const result = await response.json();
    if (!response.ok) {
        throw new Error(result.error || 'Vault kayıt listesi alınamadı');
    }

    return (result.records || []).map(record => ({
        ...record,
        source: 'vault'
    }));
}

function renderRecentSaves(items = visibleRecentSaves) {
    const container = document.getElementById('recent-saves-list');
    if (!container) return;

    if (!items.length) {
        container.innerHTML = '<p class="recent-empty">Henüz kayıt yok.</p>';
        return;
    }

    container.innerHTML = items.map((item, index) => {
        const isRectification = item.source_type === 'rectification_events';
        const lifeEvents = item.life_events || item.rectification || {};
        const hasLifeEvents = Boolean(item.has_life_events || item.has_rectification || item.life_events || item.rectification);
        const birthBase = item.birth_base || (lifeEvents && lifeEvents.birth_base) || {};
        const chartBirth = (item.chart && item.chart.birth) || {};
        const timeStatus = [
            birthBase.time_confidence,
            chartBirth.time_confidence,
            chartBirth.time_confidence_label,
            chartBirth.rectification_status
        ].map(value => String(value || '').trim().toLocaleLowerCase('tr-TR'));
        const isRectifiedChart = timeStatus.some(value => (
            value === 'rectified' ||
            value === 'rektifiye' ||
            value === 'rektifiye edilmiş' ||
            value === 'rektifiye edilmis' ||
            value === 'yapıldı'
        ));
        const label = isRectification
            ? 'Olay Kaydı'
            : (isRectifiedChart ? 'Rektifiye Harita' : (hasLifeEvents ? 'Harita + Olaylar' : 'Harita'));
        return `<article class="recent-save-item">
            <button type="button" class="recent-save-name" data-recent-index="${index}">
                ${escapeHTML(item.name || 'İsimsiz')}
                <span class="recent-save-type">${escapeHTML(label)}</span>
            </button>
            <button type="button" class="recent-save-delete" data-recent-index="${index}" aria-label="${escapeHTML(item.name || 'Kişi')} kaydını sil">
                Sil
            </button>
        </article>`;
    }).join('');
}

function setFormFieldValue(id, value) {
    const field = document.getElementById(id);
    if (!field || value === undefined || value === null || value === '') return;
    field.value = String(value);
}

function parseChartDateParts(dateText) {
    const match = String(dateText || '').match(/^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$/);
    if (!match) return null;
    return {
        day: Number(match[1]),
        month: Number(match[2]),
        year: Number(match[3])
    };
}

function parseChartTimeParts(timeText) {
    const match = String(timeText || '').match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?/);
    if (!match) return null;
    return {
        hour: Number(match[1]),
        minute: Number(match[2]),
        second: Number(match[3] || 0)
    };
}

function setCoordinateField(valueId, directionId, value, positiveDirection, negativeDirection) {
    const input = document.getElementById(valueId);
    const direction = document.getElementById(directionId);
    if (!input) return;
    const numeric = Number(value);
    if (Number.isFinite(numeric)) {
        input.value = Math.abs(numeric);
        if (direction) {
            direction.value = numeric < 0 ? negativeDirection : positiveDirection;
        }
    } else {
        input.value = value || '';
    }
}

function signedCoordinateValue(valueId, directionId, negativeDirection) {
    const input = document.getElementById(valueId);
    const direction = document.getElementById(directionId);
    const value = Number(input ? input.value : 0);
    if (!Number.isFinite(value)) return input ? input.value : '';
    return direction && direction.value === negativeDirection ? -Math.abs(value) : Math.abs(value);
}

function birthCoordinatePayload() {
    return {
        lat: document.getElementById('lat').value,
        lat_direction: document.getElementById('lat_direction').value,
        lon: document.getElementById('lon').value,
        lon_direction: document.getElementById('lon_direction').value
    };
}

function syncBirthFormFromChart(chart) {
    const birth = chart && chart.birth ? chart.birth : null;
    if (!birth) return;

    const date = parseChartDateParts(birth.date);
    if (date) {
        setFormFieldValue('day', date.day);
        setFormFieldValue('month', date.month);
        setFormFieldValue('year', date.year);
    }

    const time = parseChartTimeParts(birth.time);
    if (time) {
        setFormFieldValue('hour', time.hour);
        setFormFieldValue('minute', time.minute);
        setFormFieldValue('second', time.second);
    }

    setFormFieldValue('tz_offset', birth.tz_offset);
    setCoordinateField('lat', 'lat_direction', birth.latitude, 'N', 'S');
    setCoordinateField('lon', 'lon_direction', birth.longitude_geo, 'E', 'W');
    setFormFieldValue('city-select', '');
    setFormFieldValue('birth-place-search', birth.place || '');
    setFormFieldValue(
        'birth-time-status',
        birth.rectification_status === 'yapıldı'
            ? 'rectified'
            : birth.time_confidence === 'unknown' || birth.time_confidence === 'low'
            ? 'unknown'
            : 'known'
    );
}

function numbersNearlyEqual(left, right, tolerance = 0.0001) {
    return Number.isFinite(left) && Number.isFinite(right) && Math.abs(left - right) <= tolerance;
}

function normalizeBirthPlaceText(value) {
    return String(value || '')
        .trim()
        .toLocaleLowerCase('tr-TR')
        .replace(/\s+/g, ' ');
}

function turkeyBirthPlaceLabel(city) {
    return `${city.name} Merkez, Türkiye`;
}

function turkeyBirthPlaceAliases(city) {
    return [
        city.name,
        `${city.name} merkez`,
        `${city.name}, türkiye`,
        turkeyBirthPlaceLabel(city),
        `${city.plate} - ${city.name} merkez`,
    ].map(normalizeBirthPlaceText);
}

function findTurkeyBirthPlace(value) {
    const normalized = normalizeBirthPlaceText(value);
    if (!normalized) return null;
    return TURKEY_BIRTH_PLACES.find(city => turkeyBirthPlaceAliases(city).includes(normalized)) || null;
}

function findTurkeyProvinceFromPlace(value) {
    const normalized = normalizeBirthPlaceText(value);
    if (!normalized) return null;
    const exact = findTurkeyBirthPlace(value);
    if (exact) return exact;

    const parts = normalized
        .split(',')
        .map(part => part.trim())
        .filter(Boolean);
    const candidates = parts.length ? parts : [normalized];
    return TURKEY_BIRTH_PLACES.find(city => {
        const cityName = normalizeBirthPlaceText(city.name);
        return candidates.some(part => part === cityName || part.endsWith(` ${cityName}`));
    }) || null;
}

function populateTurkeyBirthPlaces() {
    const datalist = document.getElementById('birth-place-options');
    if (datalist) {
        datalist.innerHTML = '';
        TURKEY_BIRTH_PLACES.forEach(city => {
            const option = document.createElement('option');
            option.value = turkeyBirthPlaceLabel(city);
            option.label = `${city.plate} - ${city.name} Merkez`;
            datalist.appendChild(option);
        });
    }

    const panchangaDatalist = document.getElementById('panchanga-place-options');
    if (panchangaDatalist) {
        panchangaDatalist.innerHTML = '';
        TURKEY_BIRTH_PLACES.forEach(city => {
            const option = document.createElement('option');
            option.value = turkeyBirthPlaceLabel(city);
            option.label = `${city.plate} - ${city.name} Merkez`;
            panchangaDatalist.appendChild(option);
        });
    }

    const citySelect = document.getElementById('city-select');
    if (!citySelect) return;
    Array.from(citySelect.querySelectorAll('optgroup')).forEach(group => {
        if (group.label === TURKEY_OPTGROUP_LABEL) {
            group.remove();
        }
    });

    const turkeyGroup = document.createElement('optgroup');
    turkeyGroup.label = TURKEY_OPTGROUP_LABEL;
    TURKEY_BIRTH_PLACES.forEach(city => {
        const option = document.createElement('option');
        option.value = city.name;
        option.textContent = `${city.plate} - ${city.name} Merkez`;
        option.dataset.place = turkeyBirthPlaceLabel(city);
        option.dataset.lat = city.lat;
        option.dataset.lon = city.lon;
        option.dataset.tz = '3';
        option.dataset.timezoneId = TURKEY_TIMEZONE_ID;
        turkeyGroup.appendChild(option);
    });

    const firstInternational = Array.from(citySelect.children)
        .find(child => child.tagName === 'OPTGROUP');
    citySelect.insertBefore(turkeyGroup, firstInternational || null);
}

function selectedBirthPlaceLabel() {
    const search = document.getElementById('birth-place-search');
    const city = search ? findTurkeyBirthPlace(search.value) : null;
    if (city) return turkeyBirthPlaceLabel(city);
    const typedPlace = search ? search.value.trim() : '';
    if (typedPlace) return typedPlace;

    const citySelect = document.getElementById('city-select');
    const option = citySelect && citySelect.selectedOptions ? citySelect.selectedOptions[0] : null;
    return option && option.value ? (option.dataset.place || option.textContent.trim()) : '';
}

function panchangaReferenceForForm(defaultTimezoneId, defaultTzOffset) {
    const date = document.getElementById('panchanga-date').value;
    if (!date) return undefined;
    const placeInput = document.getElementById('panchanga-place').value.trim();
    const city = findTurkeyProvinceFromPlace(placeInput);
    const customLat = document.getElementById('panchanga-lat').value;
    const customLon = document.getElementById('panchanga-lon').value;
    const latitude = customLat || (city ? city.lat : document.getElementById('lat').value);
    const longitude = customLon || (city ? city.lon : document.getElementById('lon').value);
    const timezoneId = document.getElementById('panchanga-timezone-id').value.trim() || (city ? TURKEY_TIMEZONE_ID : defaultTimezoneId) || undefined;
    const usesBirthCoordinates = !customLat && !customLon && !city;

    return {
        date,
        time: document.getElementById('panchanga-time').value || '12:00',
        timezone_id: timezoneId,
        tz_offset: timezoneId ? undefined : defaultTzOffset,
        lat: latitude,
        lat_direction: usesBirthCoordinates ? document.getElementById('lat_direction').value : undefined,
        lon: longitude,
        lon_direction: usesBirthCoordinates ? document.getElementById('lon_direction').value : undefined,
        place: placeInput || selectedBirthPlaceLabel()
    };
}

function applyPanchangaTurkeyPlace(value) {
    const city = findTurkeyProvinceFromPlace(value);
    if (!city) return false;
    const placeInput = document.getElementById('panchanga-place');
    if (placeInput && !placeInput.value.trim()) {
        placeInput.value = turkeyBirthPlaceLabel(city);
    }
    document.getElementById('panchanga-lat').value = city.lat;
    document.getElementById('panchanga-lon').value = city.lon;
    document.getElementById('panchanga-timezone-id').value = TURKEY_TIMEZONE_ID;
    return true;
}

function applyTurkeyBirthPlace(city) {
    if (!city) return;
    const citySelect = document.getElementById('city-select');
    const search = document.getElementById('birth-place-search');
    if (search) {
        search.value = turkeyBirthPlaceLabel(city);
    }
    if (citySelect) {
        citySelect.value = city.name;
    }
    setCoordinateField('lat', 'lat_direction', city.lat, 'N', 'S');
    setCoordinateField('lon', 'lon_direction', city.lon, 'E', 'W');
    document.getElementById('tz_offset').value = '3';
    syncTimezoneOffsetFromSelectedCity();
}

function selectedCityTimezoneId() {
    const search = document.getElementById('birth-place-search');
    if (search && findTurkeyBirthPlace(search.value)) {
        return TURKEY_TIMEZONE_ID;
    }

    const citySelect = document.getElementById('city-select');
    const option = citySelect && citySelect.selectedOptions ? citySelect.selectedOptions[0] : null;
    if (option && option.dataset.timezoneId) {
        return option.dataset.timezoneId;
    }
    const group = option ? option.parentElement : null;
    if (group && group.tagName === 'OPTGROUP' && group.label === TURKEY_OPTGROUP_LABEL) {
        return TURKEY_TIMEZONE_ID;
    }
    if (option && option.value) {
        return '';
    }

    const lat = Number(signedCoordinateValue('lat', 'lat_direction', 'S'));
    const lon = Number(signedCoordinateValue('lon', 'lon_direction', 'W'));
    const looksLikeTurkey = (
        lat >= TURKEY_LAT_RANGE[0] &&
        lat <= TURKEY_LAT_RANGE[1] &&
        lon >= TURKEY_LON_RANGE[0] &&
        lon <= TURKEY_LON_RANGE[1]
    );
    return looksLikeTurkey ? TURKEY_TIMEZONE_ID : '';
}

function formDateTimeParts() {
    return {
        year: Number(document.getElementById('year').value),
        month: Number(document.getElementById('month').value),
        day: Number(document.getElementById('day').value),
        hour: Number(document.getElementById('hour').value || 0),
        minute: Number(document.getElementById('minute').value || 0),
        second: Number(document.getElementById('second').value || 0),
    };
}

function browserTimezoneOffsetHours(timezoneId, parts) {
    if (!timezoneId || !parts.year || !parts.month || !parts.day) return null;
    try {
        const utcGuess = new Date(Date.UTC(parts.year, parts.month - 1, parts.day, parts.hour, parts.minute, parts.second || 0));
        const formatter = new Intl.DateTimeFormat('en-CA', {
            timeZone: timezoneId,
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hourCycle: 'h23'
        });
        const localParts = Object.fromEntries(
            formatter.formatToParts(utcGuess)
                .filter(part => part.type !== 'literal')
                .map(part => [part.type, Number(part.value)])
        );
        const localAsUtc = Date.UTC(
            localParts.year,
            localParts.month - 1,
            localParts.day,
            localParts.hour,
            localParts.minute,
            localParts.second || 0
        );
        return (localAsUtc - utcGuess.getTime()) / 3600000;
    } catch (err) {
        return null;
    }
}

function syncTimezoneOffsetFromSelectedCity() {
    const timezoneId = selectedCityTimezoneId();
    if (!timezoneId) return;
    const offset = browserTimezoneOffsetHours(timezoneId, formDateTimeParts());
    if (offset === null) return;
    const offsetSelect = document.getElementById('tz_offset');
    offsetSelect.value = String(offset);
}

function localISODate(date = new Date()) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function localHHMM(date = new Date()) {
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    return `${hour}:${minute}`;
}

function buildLifePeriodQuery(person, timezoneId) {
    const params = new URLSearchParams({
        person_id: person.name || '',
        birth_date: [
            document.getElementById('year').value,
            String(document.getElementById('month').value).padStart(2, '0'),
            String(document.getElementById('day').value).padStart(2, '0')
        ].join('-'),
        birth_time: [
            String(document.getElementById('hour').value || '0').padStart(2, '0'),
            String(document.getElementById('minute').value || '0').padStart(2, '0'),
            String(document.getElementById('second').value || '0').padStart(2, '0')
        ].join(':'),
        birth_place: `${signedCoordinateValue('lat', 'lat_direction', 'S')},${signedCoordinateValue('lon', 'lon_direction', 'W')}`,
        from_age: '1',
        to_date: localISODate(),
        ayanamsa: 'Lahiri',
        zodiac: 'sidereal',
        house_reference: 'lagna_and_moon',
        planets: 'saturn,jupiter',
        include_dasha: 'true',
        include_antardasha: 'true',
        include_pratyantardasha: 'false',
        include_retrograde: 'true',
        include_natal_contacts: 'true',
        include_vedic_aspects: 'true'
    });
    if (timezoneId) {
        params.set('timezone_id', timezoneId);
    } else {
        params.set('tz_offset', document.getElementById('tz_offset').value);
    }
    return params;
}

async function fetchLifePeriodAnalysis(person, timezoneId) {
    const params = buildLifePeriodQuery(person, timezoneId);
    const response = await fetch(`/vedic/life-period-analysis?${params.toString()}`);
    const result = await response.json();
    if (!response.ok) {
        throw new Error(result.error || 'Uzun dönem teknik tablo alınamadı');
    }
    return result;
}

function chartBirthMatchesCurrentForm(chart) {
    const birth = chart && chart.birth ? chart.birth : null;
    if (!birth) return false;

    const date = parseChartDateParts(birth.date);
    const time = parseChartTimeParts(birth.time);
    if (!date || !time) return false;

    return (
        Number(document.getElementById('day').value) === date.day &&
        Number(document.getElementById('month').value) === date.month &&
        Number(document.getElementById('year').value) === date.year &&
        Number(document.getElementById('hour').value) === time.hour &&
        Number(document.getElementById('minute').value) === time.minute &&
        Number(document.getElementById('second').value || 0) === time.second &&
        numbersNearlyEqual(Number(document.getElementById('tz_offset').value), Number(birth.tz_offset)) &&
        numbersNearlyEqual(Number(signedCoordinateValue('lat', 'lat_direction', 'S')), Number(birth.latitude)) &&
        numbersNearlyEqual(Number(signedCoordinateValue('lon', 'lon_direction', 'W')), Number(birth.longitude_geo))
    );
}

async function refreshRecentSaves() {
    const localItems = loadRecentSaves();
    visibleRecentSaves = localItems;
    renderRecentSaves();

    try {
        const vaultItems = await loadVaultSaveItems();
        visibleRecentSaves = mergeRecentAndVaultSaves(localItems, vaultItems);
        renderRecentSaves();
    } catch (err) {
        if (!localItems.length) {
            const container = document.getElementById('recent-saves-list');
            if (container) {
                container.innerHTML = `<p class="recent-empty">${escapeHTML(err.message)}</p>`;
            }
        }
    }
}

async function showRecentChart(item, chart) {
    lastChartData = chart;
    lastPersonInfo = {
        name: item.name || '',
        group: item.group || 'Grup-01'
    };

    document.getElementById('person-name').value = lastPersonInfo.name;
    document.getElementById('group-name').value = lastPersonInfo.group;
    syncBirthFormFromChart(chart);
    document.getElementById('btn-save-vault').disabled = false;
    loadRectificationEventsForCurrentPerson();
    if (!lastChartData.life_period_analysis) {
        try {
            const timezoneId = lastChartData.birth ? lastChartData.birth.timezone_id : null;
            lastChartData.life_period_analysis = await fetchLifePeriodAnalysis(lastPersonInfo, timezoneId);
        } catch (lifeErr) {
            lastChartData.life_period_analysis = {
                status: 'not_available',
                error: lifeErr.message,
                technical_notes: ['Life period analysis could not be attached to this expert package.']
            };
        }
    }
    setVaultStatus(`${lastPersonInfo.name || 'Harita'} API ekranında açıldı.`, 'success');
    renderResults(chart);
}

function rectificationChartPayload(item) {
    const birth = item.birth_base || {};
    return {
        person: {
            id: item.name || null,
            name: item.name || null,
            group: item.group || 'Grup-01'
        },
        birth: {
            year: birth.year,
            month: birth.month,
            day: birth.day,
            hour: birth.hour,
            minute: birth.minute,
            second: birth.second || 0,
            tz_offset: birth.tz_offset,
            timezone_id: birth.timezone_id || undefined,
            lat: birth.lat,
            lon: birth.lon,
            place: birth.place || '',
            birth_sex: birth.birth_sex || undefined,
            time_confidence: birth.time_confidence || 'unknown'
        },
        options: {
            ayanamsa: 'Lahiri',
            zodiac: 'sidereal',
            house_system: 'whole_sign',
            node_type: 'true',
            language: 'tr',
            include_life_period_analysis: true,
            life_from_age: 1,
            life_to_date: localISODate()
        }
    };
}

async function openRectificationRecentSave(item) {
    if (!item.birth_base) {
        setVaultStatus('Bu rektifikasyon kaydında harita açmak için doğum bilgisi bulunamadı.', 'error');
        return;
    }
    activeRectificationRecord = item;

    setVaultStatus(`${item.name || 'Kişi'} haritası API’de açılıyor...`, '');
    const response = await fetch('/api/v2/chart/full', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(rectificationChartPayload(item))
    });
    const result = await response.json();
    if (!response.ok) {
        throw new Error(result.error || 'Harita açılamadı');
    }

    const updatedItem = {
        ...item,
        chart: result
    };
    activeRectificationRecord = updatedItem;
    await showRecentChart(updatedItem, result);
    const rectifiedTime = document.getElementById('rectified-time');
    if (rectifiedTime && result.birth && result.birth.time) {
        rectifiedTime.value = result.birth.time.slice(0, 8);
    }
    if (Array.isArray(item.events) && item.events.length) {
        setRectificationEventRows(item.events, true);
        activateTab('rectification');
    }
}

async function openRecentSave(index) {
    const items = visibleRecentSaves.length ? visibleRecentSaves : loadRecentSaves();
    const item = items[index];
    if (!item) return;

    if (item.source_type === 'rectification_events') {
        try {
            await openRectificationRecentSave(item);
        } catch (err) {
            setVaultStatus(err.message, 'error');
        }
        return;
    }

    if (item.chart) {
        await showRecentChart(item, item.chart);
        return;
    }

    const personPath = item.paths && (item.paths.person || item.paths.natal || item.paths.legacy_natal);
    if (!personPath && !item.name) {
        setVaultStatus('Bu kayıt açılacak kişi dosyası içermiyor.', 'error');
        return;
    }

    setVaultStatus(`${item.name || 'Harita'} yükleniyor...`, '');
    try {
        const response = await fetch('/api/v2/vault/load', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                path: personPath,
                name: item.name,
                group: item.group
            })
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Kayıt açılamadı');
        }

        const updatedItem = {
            ...item,
            name: result.person && result.person.name ? result.person.name : item.name,
            group: result.person && result.person.group ? result.person.group : item.group,
            chart: result.chart,
            has_life_events: Boolean(result.has_life_events || result.has_rectification),
            life_events: result.life_events || result.rectification || item.life_events || item.rectification,
            has_rectification: Boolean(result.has_rectification || result.has_life_events),
            rectification: result.rectification || result.life_events || item.rectification || item.life_events,
            birth_base: (result.life_events || result.rectification) ? (result.life_events || result.rectification).birth_base : item.birth_base,
            birth_window: (result.life_events || result.rectification) ? (result.life_events || result.rectification).birth_window : item.birth_window,
            source_docs: (result.life_events || result.rectification) ? (result.life_events || result.rectification).source_docs : item.source_docs,
            events: (result.life_events || result.rectification) ? (result.life_events || result.rectification).events : item.events,
            search_window: (result.life_events || result.rectification) ? (result.life_events || result.rectification).search_window : item.search_window
        };
        items[index] = updatedItem;
        visibleRecentSaves = items;
        if (item.source !== 'vault') {
            persistRecentSaves(visibleRecentSaves.filter(existing => existing.source !== 'vault'));
        }
        renderRecentSaves();
        await showRecentChart(updatedItem, result.chart);
        if (updatedItem.has_rectification && Array.isArray(updatedItem.events) && updatedItem.events.length) {
            activeRectificationRecord = updatedItem;
            setRectificationEventRows(updatedItem.events, true);
        }
    } catch (err) {
        setVaultStatus(err.message, 'error');
    }
}

async function deleteRecentSave(index) {
    const items = visibleRecentSaves.length ? visibleRecentSaves : loadRecentSaves();
    const item = items[index];
    if (!item) return;

    const personName = item.name || '';
    const groupName = item.group || 'Grup-01';
    if (!personName) {
        setVaultStatus('Silinecek kişi adı bulunamadı.', 'error');
        return;
    }

    const isRectification = item.source_type === 'rectification_events';
    const targetLabel = isRectification ? 'rektifikasyon kaydı' : 'kişi dosyası';
    const confirmed = window.confirm(`${personName} ${targetLabel} vaulttan silinsin mi?`);
    if (!confirmed) return;

    setVaultStatus(`${personName} siliniyor...`, '');
    try {
        const response = await fetch('/api/v2/vault/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: personName,
                group: groupName,
                record_type: isRectification ? 'rectification' : undefined
            })
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Kişi silinemedi');
        }

        const deletedKey = recentSaveKey(item);
        const remainingLocal = loadRecentSaves()
            .filter(existing => recentSaveKey(existing) !== deletedKey)
            .filter(existing => !(existing.name === personName && (existing.group || 'Grup-01') === groupName));
        persistRecentSaves(remainingLocal);
        visibleRecentSaves = visibleRecentSaves
            .filter(existing => recentSaveKey(existing) !== deletedKey)
            .filter(existing => !(existing.name === personName && (existing.group || 'Grup-01') === groupName));

        if (lastPersonInfo && lastPersonInfo.name === personName && lastPersonInfo.group === groupName) {
            lastChartData = null;
            lastPersonInfo = null;
            document.getElementById('btn-save-vault').disabled = true;
        }

        renderRecentSaves();
        setVaultStatus(`${personName} vaulttan silindi.`, 'success');
        refreshRecentSaves();
    } catch (err) {
        setVaultStatus(err.message, 'error');
    }
}

function bindRecentSaves() {
    const container = document.getElementById('recent-saves-list');
    if (!container) return;

    container.addEventListener('click', event => {
        const deleteButton = event.target.closest('.recent-save-delete');
        if (deleteButton && container.contains(deleteButton)) {
            deleteRecentSave(Number(deleteButton.dataset.recentIndex));
            return;
        }

        const button = event.target.closest('.recent-save-name');
        if (!button || !container.contains(button)) return;
        openRecentSave(Number(button.dataset.recentIndex));
    });
}

function addRecentSave(result, person) {
    const paths = result.paths || {};
    const item = {
        name: person.name,
        group: person.group,
        saved_at: new Date().toLocaleString('tr-TR'),
        paths,
        obsidian_links: result.obsidian_links || {},
        wiki_links: result.wiki_links || {},
        chart: lastChartData
    };
    const items = upsertRecentSaveItem(item);
    visibleRecentSaves = mergeRecentAndVaultSaves(items, visibleRecentSaves.filter(existing => existing.source === 'vault'));
    renderRecentSaves();
}

function renderVaultSaveError(result) {
    const status = document.getElementById('vault-status');
    const existing = Array.isArray(result.existing) && result.existing.length;

    status.classList.add('error');
    status.classList.remove('success');
    status.textContent = existing
        ? `${result.error || 'Vault kaydı yapılamadı'}: mevcut dosya var.`
        : (result.error || 'Vault kaydı yapılamadı.');
}

function escapeHTML(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function formatQualityValue(value) {
    const translations = {
        known: 'biliniyor',
        unknown: 'bilinmiyor',
        high: 'yüksek',
        medium: 'orta',
        low: 'düşük',
        very_low: 'çok düşük',
        moon_lagna: 'Ay Lagna referansı',
        rectified: 'rektifiye edildi',
        not_rectified: 'rektifiye edilmedi',
        'yapıldı': 'yapıldı',
        'yapılmadı': 'yapılmadı'
    };
    if (Array.isArray(value)) {
        return value.length ? value.map(item => translations[item] || item).map(escapeHTML).join(', ') : 'Yok';
    }
    if (typeof value === 'boolean') {
        return value ? 'Evet' : 'Hayır';
    }
    if (value === null || value === undefined || value === '') {
        return 'Belirtilmedi';
    }
    if (translations[value]) {
        return escapeHTML(translations[value]);
    }
    return escapeHTML(value);
}

function renderDataQuality(data) {
    const container = document.getElementById('quality-content');
    if (!container) return;

    const quality = data.data_quality || {};
    const missing = Array.isArray(data.missing) ? data.missing : [];
    const qualityItems = [
        ['Doğum Saati', quality.birth_time_confidence_label || quality.birth_time_confidence],
        ['Rektifikasyon', quality.rectification_status],
        ['Rektifikasyon Kaynağı', quality.rectification_source_label || quality.rectification_source],
        ['Hesap Durumu', quality.calculation_status],
        ['Lagna Yorumu Güveni', quality.lagna_interpretation_confidence],
        ['Ev Yorumu Güveni', quality.house_interpretation_confidence],
        ['Gezegen Burçları Güveni', quality.planet_sign_interpretation_confidence],
        ['Referans', quality.fallback_reference],
        ['Eksik Alanlar', quality.missing_fields],
    ];

    const qualityRows = qualityItems
        .filter(([, value]) => value !== undefined && value !== null && value !== '')
        .map(([label, value]) => `
            <div class="quality-item">
                <div class="label">${escapeHTML(label)}</div>
                <div class="value">${formatQualityValue(value)}</div>
            </div>
        `)
        .join('');

    const missingHtml = missing.length
        ? `<ul class="missing-list">
            ${missing.map(item => `
                <li>
                    <span class="missing-key">${escapeHTML(item.key || 'bilinmeyen_katman')}</span>
                    <span class="missing-detail">${escapeHTML(item.impact || item.reason || 'Henüz uygulanmadı')}</span>
                </li>
            `).join('')}
        </ul>`
        : '<p class="quality-note">Eksik katman bildirilmedi.</p>';

    container.innerHTML = `
        <div class="quality-grid">
            ${qualityRows || '<p class="quality-note">Veri kalitesi alanı bildirilmedi.</p>'}
        </div>
        <div class="missing-section">
            <div class="quality-section-title">Eksik Katmanlar${missing.length ? ` (${missing.length})` : ''}</div>
            ${missingHtml}
        </div>
    `;
}

function renderSummary(data) {
    const bi = data.birth || data.birth_info;
    const l = data.lagna;
    const nak = l.nakshatra;
    const ayanamsa = data.meta ? data.meta.ayanamsa : data.ayanamsa;
    const timezone = bi.timezone_label || bi.timezone;
    const lat = bi.latitude;
    const lon = bi.longitude_geo;
    const lagnaSign = l.sign_tr ? `${l.sign_tr} (${l.sign})` : l.sign;

    const html = `
        <div class="summary-item">
            <div class="label">Doğum</div>
            <div class="value">${bi.date} — ${bi.time}</div>
        </div>
        <div class="summary-item">
            <div class="label">Saat Dilimi</div>
            <div class="value">${timezone}</div>
        </div>
        <div class="summary-item">
            <div class="label">Koordinatlar</div>
            <div class="value">${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E</div>
        </div>
        <div class="summary-item">
            <div class="label">Ayanamsa</div>
            <div class="value">${ayanamsa.type} (${ayanamsa.value}°)</div>
        </div>
        <div class="summary-item">
            <div class="label">Lagna (Ascendant)</div>
            <div class="value gold">${lagnaSign} — ${l.degree_str}</div>
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
        retrograde: p.motion ? p.motion.retrograde : p.retrograde
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
    const navamshaLagna = data.vargas ? data.vargas.D9.lagna : data.navamsha_lagna;
    const planets = data.planets.map(p => ({
        abbr: p.abbr,
        sign_index: p.varga_status ? p.varga_status.D9.sign_index : p.navamsha_sign_index,
        retrograde: p.motion ? p.motion.retrograde : p.retrograde
    }));
    // Navamsha Lagna
    planets.push({
        abbr: 'Asc',
        sign_index: navamshaLagna.sign_index,
        retrograde: false
    });

    drawSouthIndianChart('d9-chart', planets, navamshaLagna.sign_index, 'D9 Navamsha');
}

function renderVargaChart(data, division, containerId, title) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const varga = data.vargas && data.vargas[division];
    if (!varga || !varga.lagna || !Array.isArray(varga.planets)) {
        container.innerHTML = '<div class="empty-chart-note">Bu varga verisi API yanıtında yok.</div>';
        return;
    }

    const planets = varga.planets.map(p => ({
        abbr: p.abbr,
        sign_index: p.sign_index,
        retrograde: false
    }));
    planets.push({
        abbr: 'Asc',
        sign_index: varga.lagna.sign_index,
        retrograde: false
    });

    drawSouthIndianChart(containerId, planets, varga.lagna.sign_index, title);
}

function renderVargaPanel(data, division) {
    const container = document.getElementById('varga-detail-chart');
    const tbody = document.querySelector('#varga-detail-table tbody');
    if (!container || !tbody) return;

    const availableDivision = VARGA_DIVISIONS.find(key => data.vargas && data.vargas[key]);
    const selectedDivision = data.vargas && data.vargas[division] ? division : availableDivision;
    const tabs = document.querySelectorAll('.varga-tab');

    tabs.forEach(tab => {
        const isAvailable = Boolean(data.vargas && data.vargas[tab.dataset.varga]);
        const isActive = tab.dataset.varga === selectedDivision;
        tab.disabled = !isAvailable;
        tab.classList.toggle('active', isActive);
        tab.setAttribute('aria-selected', String(isActive));
    });

    if (!selectedDivision) {
        container.innerHTML = '<div class="empty-chart-note">Varga verisi API yanıtında yok.</div>';
        tbody.innerHTML = '<tr><td colspan="3">Varga verisi yok</td></tr>';
        return;
    }

    activeVargaDivision = selectedDivision;
    const varga = data.vargas[selectedDivision];
    const title = VARGA_TITLES[selectedDivision] || `${selectedDivision} ${varga.name || ''}`.trim();
    renderVargaChart(data, selectedDivision, 'varga-detail-chart', title);

    const rows = [];
    if (varga.lagna) {
        const lagnaSign = varga.lagna.sign_tr
            ? `${varga.lagna.sign_tr} (${varga.lagna.sign})`
            : varga.lagna.sign;
        rows.push(`<tr>
            <td style="font-weight:600;color:#c9a227">Lagna</td>
            <td>${escapeHTML(lagnaSign)}</td>
            <td>${escapeHTML(varga.lagna.degree_str)}</td>
        </tr>`);
    }

    for (const p of varga.planets || []) {
        const sign = p.sign_tr ? `${p.sign_tr} (${p.sign})` : p.sign;
        rows.push(`<tr>
            <td class="planet-${escapeHTML(p.abbr)}" style="font-weight:600">${escapeHTML(p.name)}</td>
            <td>${escapeHTML(sign)}</td>
            <td>${escapeHTML(p.degree_str)}</td>
        </tr>`);
    }

    tbody.innerHTML = rows.join('') || '<tr><td colspan="3">Varga pozisyonu yok</td></tr>';
}

function formatBoolean(value) {
    return value ? '<span class="status-badge success">Evet</span>' : '<span class="status-badge muted">Hayır</span>';
}

function formatCombustion(combustion) {
    if (!combustion) return '';
    if (combustion.severity === 'not_calculated') {
        return '<span class="status-badge muted">Hesaplanmaz</span>';
    }
    if (!combustion.is_combust) {
        return '<span class="status-badge muted">Yok</span>';
    }
    return `<span class="status-badge danger">${combustion.severity}</span>`;
}

function formatWar(war) {
    if (!war) return '';
    if (war.status === 'not_applicable') {
        return '<span class="status-badge muted">Uygulanmaz</span>';
    }
    if (!war.in_graha_yuddha) {
        return '<span class="status-badge muted">Yok</span>';
    }
    const orb = typeof war.orb === 'number' ? ` ${war.orb.toFixed(2)}°` : '';
    return `<span class="status-badge danger">${war.opponent}${orb}</span>`;
}

function renderPlanetsTable(data) {
    const tbody = document.querySelector('#planets-table tbody');
    const angleOrder = ['lagna', 'mc', 'dsc'];
    const angles = data.angles || {};
    let rows = angleOrder
        .filter(key => angles[key])
        .map(key => {
            const point = angles[key];
            const label = point.name || key.toUpperCase();
            const sign = point.sign_tr ? `${point.sign_tr} (${point.sign})` : point.sign;
            return `<tr class="angle-row">
                <td style="font-weight:700">${escapeHTML(label)}</td>
                <td>${escapeHTML(sign || '-')}</td>
                <td>${escapeHTML(point.degree_str || '-')}</td>
                <td>${escapeHTML(point.house || '-')}</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td></td>
            </tr>`;
        })
        .join('');
    for (const p of data.planets) {
        const retrograde = p.motion ? p.motion.retrograde : p.retrograde;
        const retro = retrograde
            ? '<span class="retro-badge">R</span>'
            : '';
        const d9 = p.varga_status
            ? `${p.varga_status.D9.sign_tr} (${p.varga_status.D9.sign})`
            : p.navamsha_sign;
        const dignity = p.dignity
            ? `${p.dignity.essential} / ${p.dignity.natural_friendship}`
            : '';
        rows += `<tr>
            <td class="planet-${p.abbr}" style="font-weight:600">${p.name}</td>
            <td>${p.sign_tr ? `${p.sign_tr} (${p.sign})` : p.sign}</td>
            <td>${p.degree_str}</td>
            <td>${p.house}</td>
            <td>${d9}</td>
            <td>${dignity}</td>
            <td>${formatCombustion(p.combustion)}</td>
            <td>${formatWar(p.war)}</td>
            <td>${formatBoolean(p.varga_status && p.varga_status.vargottama)}</td>
            <td>${retro}</td>
        </tr>`;
    }
    tbody.innerHTML = rows;
}

function renderNakshatraTable(data) {
    const tbody = document.querySelector('#nakshatra-table tbody');
    const angleOrder = ['lagna', 'mc', 'dsc'];
    const angles = data.angles || {};
    let rows = angleOrder
        .filter(key => angles[key] && angles[key].nakshatra)
        .map(key => {
            const point = angles[key];
            const n = point.nakshatra;
            return `<tr class="angle-row">
                <td style="font-weight:700">${escapeHTML(point.name || key.toUpperCase())}</td>
                <td>${escapeHTML(n.name || '-')}</td>
                <td>${escapeHTML(n.pada || '-')}</td>
                <td>${escapeHTML(n.lord || '-')}</td>
            </tr>`;
        })
        .join('');
    for (const p of data.planets) {
        const n = p.nakshatra;
        rows += `<tr>
            <td class="planet-${p.abbr}" style="font-weight:600">${escapeHTML(p.name)}</td>
            <td>${escapeHTML(n.name)}</td>
            <td>${escapeHTML(n.pada)}</td>
            <td>${escapeHTML(n.lord)}</td>
        </tr>`;
    }
    tbody.innerHTML = rows;
}

function renderNavamshaTable(data) {
    const tbody = document.querySelector('#navamsha-table tbody');
    const navamshaLagna = data.vargas ? data.vargas.D9.lagna : data.navamsha_lagna;
    let rows = `<tr>
        <td style="font-weight:600;color:#c9a227">Lagna (D9)</td>
        <td>${navamshaLagna.sign_tr ? `${navamshaLagna.sign_tr} (${navamshaLagna.sign})` : navamshaLagna.sign}</td>
        <td>${navamshaLagna.degree_str}</td>
    </tr>`;
    for (const p of data.planets) {
        const d9 = p.varga_status ? p.varga_status.D9 : {
            sign: p.navamsha_sign,
            degree_str: p.navamsha_degree_str
        };
        rows += `<tr>
            <td class="planet-${p.abbr}" style="font-weight:600">${p.name}</td>
            <td>${d9.sign_tr ? `${d9.sign_tr} (${d9.sign})` : d9.sign}</td>
            <td>${d9.degree_str}</td>
        </tr>`;
    }
    tbody.innerHTML = rows;
}

function renderAspectsTable(data) {
    const tbody = document.querySelector('#aspects-table tbody');
    const aspects = data.aspects ? data.aspects.graha_drishti : [];
    let rows = '';
    for (const a of aspects) {
        rows += `<tr>
            <td style="font-weight:600">${a.from}</td>
            <td>${a.aspect_type}</td>
            <td>${a.to_house}</td>
            <td>${a.to_sign}</td>
            <td>${a.to_planets.length ? a.to_planets.join(', ') : '-'}</td>
        </tr>`;
    }
    tbody.innerHTML = rows || '<tr><td colspan="5">Kayıt yok</td></tr>';
}

function formatYogaLabel(value) {
    if (!value) return '-';
    return String(value).replace(/_/g, ' ');
}

function renderYogaFactors(title, factors) {
    const list = Array.isArray(factors) ? factors : [];
    const items = list.length
        ? list.map(factor => {
            const detail = factor && factor.detail
                ? `<code>${escapeHTML(JSON.stringify(factor.detail))}</code>`
                : '';
            return `<li>
                <span>${escapeHTML(factor.code || 'factor')}</span>
                <small>${escapeHTML(factor.source || '')}</small>
                ${detail}
            </li>`;
        }).join('')
        : '<li class="empty-factor">Yok</li>';

    return `<div class="yoga-factor-group">
        <h4>${escapeHTML(title)}</h4>
        <ul>${items}</ul>
    </div>`;
}

function renderYogas(data) {
    const container = document.getElementById('yogas-list');
    if (!container) return;

    const matches = data.yogas && Array.isArray(data.yogas.matches)
        ? data.yogas.matches
        : [];

    if (!matches.length) {
        container.innerHTML = '<p class="yoga-empty">Eşleşen yoga yok</p>';
        return;
    }

    container.innerHTML = matches.map(match => `
        <article class="yoga-card">
            <div class="yoga-card-header">
                <div>
                    <h3>${escapeHTML(match.name || 'Yoga')}</h3>
                    <p>${escapeHTML(match.rule || '')}</p>
                </div>
                <div class="yoga-badges">
                    <span>${escapeHTML(formatYogaLabel(match.topic))}</span>
                    <span>${escapeHTML(formatYogaLabel(match.effect_type))}</span>
                    <span>${escapeHTML(formatYogaLabel(match.strength))}</span>
                    <span>${escapeHTML(formatYogaLabel(match.confidence))}</span>
                </div>
            </div>
            <div class="yoga-factor-grid">
                ${renderYogaFactors('Destekleyen', match.supporting_factors)}
                ${renderYogaFactors('Zorlayan', match.challenging_factors)}
                ${renderYogaFactors('İptal/Dengeleyen', match.cancellation_factors)}
            </div>
        </article>
    `).join('');
}

function renderSpecialLagnas(data) {
    const container = document.getElementById('special-lagnas-content');
    if (!container) return;

    const specialLagnas = data.special_lagnas || {};
    const entries = SPECIAL_LAGNA_ORDER
        .filter(key => specialLagnas[key])
        .map(key => specialLagnas[key]);

    if (!entries.length) {
        container.innerHTML = '<p class="special-lagnas-empty">Özel lagna verisi yok</p>';
        return;
    }

    const rows = entries.map(item => {
        const sign = item.sign_tr
            ? `${item.sign_tr} (${item.sign || ''})`
            : (item.sign || '-');
        return `<tr>
            <td>${escapeHTML(item.name || '-')}</td>
            <td>${escapeHTML(sign)}</td>
            <td>${escapeHTML(item.degree_str || '-')}</td>
            <td><span class="special-lagna-confidence">${escapeHTML(item.confidence || '-')}</span></td>
            <td class="special-lagna-source">${escapeHTML(item.source || '-')}</td>
        </tr>`;
    }).join('');

    container.innerHTML = `
        <div class="table-wrapper">
            <table class="data-table special-lagnas-table">
                <thead>
                    <tr>
                        <th>Ad</th>
                        <th>Burç</th>
                        <th>Derece</th>
                        <th>Güven</th>
                        <th>Kaynak</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
}

function signLabel(item) {
    if (!item) return '-';
    return item.sign_tr ? `${item.sign_tr} (${item.sign || ''})` : (item.sign || '-');
}

function renderLayerMeta(item) {
    if (!item) return '';
    const bits = [];
    if (item.status) bits.push(['Durum', item.status]);
    if (item.confidence) bits.push(['Güven', item.confidence]);
    if (item.method) bits.push(['Yöntem', item.method]);
    return bits.length ? `
        <div class="layer-meta">
            ${bits.map(([label, value]) => `
                <div>
                    <span>${escapeHTML(label)}</span>
                    <strong>${escapeHTML(value)}</strong>
                </div>
            `).join('')}
        </div>
    ` : '';
}

function renderAshtakavarga(data) {
    const container = document.getElementById('ashtakavarga-content');
    if (!container) return;
    const layer = data.ashtakavarga;
    const bhavaBala = data.bhava_bala || {};
    if (!layer || !layer.sarva) {
        container.innerHTML = '<p class="layer-empty">Ashtakavarga verisi yok.</p>';
        return;
    }

    const supportBadgeClass = (level) => {
        if (level === 'high_support') return 'status-badge success';
        if (level === 'moderate_support') return 'status-badge';
        if (level === 'low_support') return 'status-badge muted';
        if (level === 'challenging') return 'status-badge danger';
        return 'status-badge muted';
    };

    const supportLabel = (level) => ({
        high_support: 'Yüksek destek',
        moderate_support: 'Orta destek',
        low_support: 'Düşük destek',
        challenging: 'Zorlayıcı',
        not_available: '-',
    }[level] || level || '-');

    const bhavaNote = (house) => {
        const ashtakavarga = house.ashtakavarga || {};
        const lordShadbala = house.lord_shadbala || {};
        const lordship = house.lordship || {};
        const condition = lordship.condition || {};
        const changed = ((house.bhava_chalit || {}).changed_planets_touching_house || [])
            .map(item => item.planet)
            .filter(Boolean);
        const support = supportLabel(ashtakavarga.sav_support_level || 'not_available');
        const dignity = condition.dignity || '-';
        const shadbalaGrade = lordShadbala.grade || '-';
        const changedText = changed.length ? changed.join(', ') : 'yok';
        return `SAV desteği ${support}; lord dignity ${dignity}, lord Shadbala ${shadbalaGrade}, Chalit değişimi ${changedText}.`;
    };

    const sarvaRows = (layer.sarva.by_sign || []).map(row => `
        <tr>
            <td>${escapeHTML(signLabel(row))}</td>
            <td>${escapeHTML(row.house)}</td>
            <td>${escapeHTML(row.bindus)}</td>
        </tr>
    `).join('');
    const strongest = (layer.sarva.strongest_signs || [])
        .map(row => `${signLabel(row)}: ${row.bindus}`)
        .join(', ');
    const transitRows = layer.transit_scoring && Array.isArray(layer.transit_scoring.rows)
        ? layer.transit_scoring.rows.map(row => `
            <tr>
                <td>${escapeHTML(row.planet)}</td>
                <td>${escapeHTML(signLabel(row))}</td>
                <td>${escapeHTML(row.degree_str || '-')}</td>
                <td>${escapeHTML(row.sarva_bindus)}</td>
                <td>${escapeHTML(row.sarva_support_level)}</td>
                <td>${escapeHTML(row.planet_bhinna_bindus ?? '-')}</td>
            </tr>
        `).join('')
        : '';
    const trikona = layer.shodhana && layer.shodhana.trikona;
    const ekadhipatya = layer.shodhana && layer.shodhana.ekadhipatya;
    const pinda = layer.shodhana && layer.shodhana.shodhya_pinda;
    const shodhanaRows = trikona && trikona.planets
        ? Object.values(trikona.planets).map(row => `
            <tr>
                <td>${escapeHTML(row.planet)}</td>
                <td>${escapeHTML(row.total_before)}</td>
                <td>${escapeHTML(row.total_reduction)}</td>
                <td>${escapeHTML(row.total_after)}</td>
                <td>${escapeHTML(ekadhipatya && ekadhipatya.planets && ekadhipatya.planets[row.planet] ? ekadhipatya.planets[row.planet].total_reduction : '-')}</td>
                <td>${escapeHTML(ekadhipatya && ekadhipatya.planets && ekadhipatya.planets[row.planet] ? ekadhipatya.planets[row.planet].total_after : '-')}</td>
            </tr>
        `).join('')
        : '';
    const pindaRows = pinda && Array.isArray(pinda.ranking)
        ? pinda.ranking.map(row => `
            <tr>
                <td>${escapeHTML(row.planet)}</td>
                <td>${escapeHTML(row.rashi_pinda)}</td>
                <td>${escapeHTML(row.graha_pinda)}</td>
                <td>${escapeHTML(row.shodhya_pinda)}</td>
            </tr>
        `).join('')
        : '';
    const bavHeaders = expertBavHeaders(data);
    const bavRows = expertBavRows(data).map(row => `
        <tr>
            ${row.map(cell => `<td>${escapeHTML(cell)}</td>`).join('')}
        </tr>
    `).join('');
    const bhavaRows = Array.isArray(bhavaBala.houses)
        ? bhavaBala.houses.map(house => {
            const ashtakavarga = house.ashtakavarga || {};
            const lordShadbala = house.lord_shadbala || {};
            const lordship = house.lordship || {};
            const condition = lordship.condition || {};
            const changedPlanets = ((house.bhava_chalit || {}).changed_planets_touching_house || [])
                .map(item => item.planet)
                .filter(Boolean)
                .join(', ') || '-';
            return `
                <tr>
                    <td>${escapeHTML(house.house)}</td>
                    <td>${escapeHTML(signLabel(house))}</td>
                    <td>${escapeHTML(house.lord || '-')}</td>
                    <td><span class="${supportBadgeClass(ashtakavarga.sav_support_level)}">${escapeHTML(supportLabel(ashtakavarga.sav_support_level || 'not_available'))}</span></td>
                    <td>${escapeHTML(ashtakavarga.sav ?? '-')}</td>
                    <td>${escapeHTML(ashtakavarga.lord_bav ?? '-')}</td>
                    <td>${escapeHTML(lordShadbala.total_score ?? '-')}</td>
                    <td>${escapeHTML(lordShadbala.grade || '-')}</td>
                    <td>${escapeHTML(condition.dignity || '-')}</td>
                    <td>${escapeHTML(changedPlanets)}</td>
                    <td>${escapeHTML(bhavaNote(house))}</td>
                </tr>
            `;
        }).join('')
        : '';
    const bhavaSensitiveCount = Array.isArray(bhavaBala.houses)
        ? bhavaBala.houses.filter(house => ((house.bhava_chalit || {}).changed_planets_touching_house || []).length).length
        : 0;
    const bhavaSupportLeaders = Array.isArray(bhavaBala.houses)
        ? bhavaBala.houses
            .filter(house => typeof (house.ashtakavarga || {}).sav === 'number')
            .sort((a, b) => (b.ashtakavarga.sav || 0) - (a.ashtakavarga.sav || 0))
            .slice(0, 3)
            .map(house => `Ev ${house.house}: ${(house.ashtakavarga || {}).sav}`)
            .join(', ')
        : '';

    container.innerHTML = `
        ${renderLayerMeta(layer)}
        <div class="layer-summary-strip">
            <div><span>Toplam</span><strong>${escapeHTML(layer.sarva.total)}</strong></div>
            <div><span>Güçlü burçlar</span><strong>${escapeHTML(strongest || '-')}</strong></div>
            <div><span>Trikona Sonrası</span><strong>${escapeHTML(trikona && trikona.sarva_after_trikona ? trikona.sarva_after_trikona.total : '-')}</strong></div>
            <div><span>Ekadhipatya Sonrası</span><strong>${escapeHTML(ekadhipatya && ekadhipatya.sarva_after_ekadhipatya ? ekadhipatya.sarva_after_ekadhipatya.total : '-')}</strong></div>
        </div>
        <div class="layer-summary-strip">
            <div><span>BAV Kolon</span><strong>${escapeHTML(bavHeaders.length)}</strong></div>
            <div><span>Transit satırı</span><strong>${escapeHTML((layer.transit_scoring && layer.transit_scoring.rows ? layer.transit_scoring.rows.length : 0))}</strong></div>
            <div><span>Bhava Bala</span><strong>${escapeHTML(bhavaBala.status || 'not_available')}</strong></div>
            <div><span>Saat hassası</span><strong>${escapeHTML((bhavaBala.summary || {}).birth_time_sensitive ? 'Evet' : 'Hayır')}</strong></div>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Burç</th><th>Ev</th><th>Bindu</th></tr></thead>
                <tbody>${sarvaRows}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Ev</th><th>Burç</th>${bavHeaders.map(header => `<th>${escapeHTML(header)}</th>`).join('')}</tr></thead>
                <tbody>${bavRows || `<tr><td colspan="${2 + bavHeaders.length}">BAV görünümü yok</td></tr>`}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Transit</th><th>Burç</th><th>Derece</th><th>SAV</th><th>Destek</th><th>BAV</th></tr></thead>
                <tbody>${transitRows || '<tr><td colspan="6">Transit scoring yok</td></tr>'}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Gezegen</th><th>Önce</th><th>Trikona Düşüm</th><th>Trikona Sonra</th><th>Ekadhipatya Düşüm</th><th>Ekadhipatya Sonra</th></tr></thead>
                <tbody>${shodhanaRows || '<tr><td colspan="6">Shodhana yok</td></tr>'}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Gezegen</th><th>Rashi Pinda</th><th>Graha Pinda</th><th>Shodhya Pinda</th></tr></thead>
                <tbody>${pindaRows || '<tr><td colspan="4">Shodhya Pinda yok</td></tr>'}</tbody>
            </table>
        </div>
        <div class="layer-summary-strip">
            <div><span>Bhava sayısı</span><strong>${escapeHTML((bhavaBala.summary || {}).house_count ?? '-')}</strong></div>
            <div><span>Puan üretiliyor mu</span><strong>${escapeHTML((bhavaBala.summary || {}).scored ? 'Evet' : 'Hayır')}</strong></div>
            <div><span>Chalit temaslı ev</span><strong>${escapeHTML(bhavaSensitiveCount)}</strong></div>
            <div><span>Yüksek SAV</span><strong>${escapeHTML(bhavaSupportLeaders || '-')}</strong></div>
        </div>
        <div class="layer-note">Bhava Bala burada teknik kanıt tablosu olarak gösterilir; yeni ağırlıklı skor veya yorum üretilmez.</div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Ev</th><th>Burç</th><th>Lord</th><th>SAV Destek</th><th>SAV</th><th>Lord BAV</th><th>Lord Shadbala</th><th>Seviye</th><th>Dignity</th><th>Chalit Değişim</th><th>Teknik Not</th></tr></thead>
                <tbody>${bhavaRows || '<tr><td colspan="11">Bhava Bala verisi yok</td></tr>'}</tbody>
            </table>
        </div>
    `;
}

function renderShadbala(data) {
    const container = document.getElementById('shadbala-content');
    if (!container) return;
    const layer = data.shadbala;
    if (!layer || !Array.isArray(layer.planets)) {
        container.innerHTML = '<p class="layer-empty">Shadbala verisi yok.</p>';
        return;
    }

    const componentLabel = (name) => ({
        sthana_bala: 'Sthana',
        dig_bala: 'Dig',
        cheshta_bala: 'Cheshta',
        kala_bala: 'Kala',
        drik_bala: 'Drik',
        naisargika_bala: 'Naisargika',
        yuddha_bala_adjustment: 'Yuddha adj.',
    }[name] || name || '-');

    const statusLabel = (status) => ({
        sufficient: 'Yeterli',
        near_minimum: 'Sınırda',
        insufficient: 'Zayıf',
    }[status] || status || '-');

    const statusBadgeClass = (status) => {
        if (status === 'sufficient') return 'status-badge success';
        if (status === 'insufficient') return 'status-badge danger';
        if (status === 'near_minimum') return 'status-badge';
        return 'status-badge muted';
    };

    const technicalNote = (item) => {
        const professionalTotal = item.professional_total || {};
        const summary = professionalTotal.component_breakdown_summary || {};
        const strongest = componentLabel(summary.strongest_component);
        const weakest = componentLabel(summary.weakest_component);
        const status = professionalTotal.professional_status;

        if (status === 'sufficient') {
            const margin = professionalTotal.excess_rupa ?? '-';
            if ((professionalTotal.strength_ratio || 0) >= 1.25) {
                return `Minimumu net geçer; ana destek ${strongest}, zayıf halka ${weakest}, marj ${margin} rupa.`;
            }
            return `Minimumu geçer; ana destek ${strongest}, izlenecek alan ${weakest}, marj ${margin} rupa.`;
        }

        if (status === 'near_minimum') {
            const deficit = professionalTotal.deficit_rupa ?? '-';
            return `Sınıra yakın; ana destek ${strongest}, zayıf halka ${weakest}, eksik ${deficit} rupa.`;
        }

        const deficit = professionalTotal.deficit_rupa ?? '-';
        return `Minimumun altında; ana destek ${strongest}, zayıf halka ${weakest}, açık ${deficit} rupa.`;
    };

    const rows = layer.planets.map(item => `
        <tr>
            <td>${escapeHTML(item.planet)}</td>
            <td>${escapeHTML(item.total_score)}</td>
            <td><span class="status-badge">${escapeHTML(item.grade)}</span></td>
            <td>${escapeHTML(item.components.sthana_bala.score)}</td>
            <td>${escapeHTML(item.components.dig_bala.score)}</td>
            <td>${escapeHTML(item.components.cheshta_bala.score)}</td>
            <td>${escapeHTML(item.components.kala_bala ? item.components.kala_bala.score : '-')}</td>
            <td>${escapeHTML(item.components.drik_bala ? item.components.drik_bala.score : '-')}</td>
            <td>${escapeHTML(item.components.yuddha_bala ? item.components.yuddha_bala.score_adjustment : '-')}</td>
            <td>${escapeHTML(item.components.naisargika_bala.score)}</td>
        </tr>
    `).join('');

    const summary = layer.summary || {};
    const strongestPlanet = summary.strongest_planet || {};
    const weakestPlanet = summary.weakest_planet || {};
    const sufficientCount = (summary.sufficient_planets || []).length;
    const attentionCount = (summary.needs_attention || []).length;
    const noteRows = layer.planets.map(item => `
        <tr>
            <td>${escapeHTML(item.planet)}</td>
            <td><span class="${statusBadgeClass((item.professional_total || {}).professional_status)}">${escapeHTML(statusLabel((item.professional_total || {}).professional_status))}</span></td>
            <td>${escapeHTML(technicalNote(item))}</td>
        </tr>
    `).join('');

    container.innerHTML = `
        ${renderLayerMeta(layer)}
        <div class="layer-summary-strip">
            <div><span>En güçlü</span><strong>${escapeHTML(strongestPlanet.planet || '-')}</strong></div>
            <div><span>Oran</span><strong>${escapeHTML(strongestPlanet.strength_ratio ?? '-')}</strong></div>
            <div><span>En zayıf</span><strong>${escapeHTML(weakestPlanet.planet || '-')}</strong></div>
            <div><span>Dikkat</span><strong>${escapeHTML(attentionCount)}</strong></div>
        </div>
        <div class="layer-summary-strip">
            <div><span>Gezegen sayısı</span><strong>${escapeHTML(summary.planet_count ?? layer.planets.length)}</strong></div>
            <div><span>Yeterli</span><strong>${escapeHTML(sufficientCount)}</strong></div>
            <div><span>Sınır/zayıf</span><strong>${escapeHTML(attentionCount)}</strong></div>
            <div><span>Kural</span><strong>${escapeHTML(summary.summary_rule || 'professional_total')}</strong></div>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead>
                    <tr><th>Gezegen</th><th>Toplam</th><th>Seviye</th><th>Sthana</th><th>Dig</th><th>Cheshta</th><th>Kala</th><th>Drik</th><th>Yuddha Adj.</th><th>Naisargika</th></tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead>
                    <tr><th>Gezegen</th><th>Durum</th><th>Teknik Not</th></tr>
                </thead>
                <tbody>${noteRows}</tbody>
            </table>
        </div>
    `;
}

function renderDoshas(data) {
    const container = document.getElementById('doshas-content');
    if (!container) return;
    const doshas = data.doshas || {};
    const kala = doshas.kala_sarpa || {};
    const mangala = doshas.mangala || {};

    container.innerHTML = `
        <div class="layer-summary-strip">
            <div><span>Kala Sarpa</span><strong>${kala.is_present ? 'Var' : 'Yok'}</strong></div>
            <div><span>Subtype</span><strong>${escapeHTML(kala.subtype || '-')}</strong></div>
            <div><span>Mangala</span><strong>${mangala.is_present ? 'Var' : 'Yok'}</strong></div>
            <div><span>Net Şiddet</span><strong>${escapeHTML(mangala.net_severity || mangala.severity || '-')}</strong></div>
        </div>
        <div class="layer-summary-strip">
            <div><span>Kala Sarpa Yön</span><strong>${escapeHTML(kala.direction || '-')}</strong></div>
            <div><span>Axis Gücü</span><strong>${escapeHTML(kala.strength || '-')}</strong></div>
            <div><span>Containment</span><strong>${escapeHTML(kala.containment_ratio ?? '-')}</strong></div>
            <div><span>Mangala İptal</span><strong>${escapeHTML((mangala.cancellation_factors || []).length)}</strong></div>
        </div>
        <div class="layer-note">${escapeHTML((kala.notes || []).concat(mangala.notes || []).join(' '))}</div>
    `;
}

function renderJaiminiDetails(data) {
    const container = document.getElementById('jaimini-content');
    if (!container) return;
    const jaimini = data.jaimini || {};
    const chara = jaimini.chara_karakas || {};
    const arudha = jaimini.arudha || {};
    const karakamsa = jaimini.karakamsa || {};
    const swamsha = jaimini.swamsha || {};
    const padas = arudha.padas || {};
    const upapadaDetail = arudha.upapada_detail || {};
    const argala = jaimini.argala || {};
    const argalaSummary = argala.summary || {};
    const padaStrengths = arudha.pada_strengths && arudha.pada_strengths.padas
        ? arudha.pada_strengths.padas
        : {};
    const charaRows = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
        .map(role => {
            const item = chara[role] || {};
            return `
                <tr>
                    <td>${escapeHTML(role)}</td>
                    <td>${escapeHTML(item.planet || '-')}</td>
                    <td>${escapeHTML(item.sign || '-')}</td>
                    <td>${escapeHTML(item.degree_str || '-')}</td>
                    <td>${escapeHTML(item.nakshatra || '-')}</td>
                </tr>
            `;
        }).join('');
    const padaRows = ['A1', 'A2', 'A7', 'A10', 'A12']
        .filter(key => padas[key])
        .map(key => `
            <tr>
                <td>${escapeHTML(key)}</td>
                <td>${escapeHTML(signLabel(padas[key].pada))}</td>
                <td>${escapeHTML(padas[key].lord)}</td>
                <td>${escapeHTML(padaStrengths[key] ? padaStrengths[key].score : '-')}</td>
            </tr>
        `).join('');
    const argalaRows = Array.isArray(argala.sources)
        ? argala.sources.map(source => `
            <tr>
                <td>${escapeHTML(source.source)}</td>
                <td>${escapeHTML(signLabel(source.source_sign))}</td>
                <td>${escapeHTML(source.active_count)}</td>
                <td>${escapeHTML(source.obstructed_count)}</td>
                <td>${escapeHTML(source.net_score)}</td>
                <td>${escapeHTML(source.strength)}</td>
            </tr>
        `).join('')
        : '';
    const karakamsaRows = Array.isArray(karakamsa.d9_planets_from_karakamsa)
        ? karakamsa.d9_planets_from_karakamsa.map(row => `
            <tr>
                <td>${escapeHTML(row.planet)}</td>
                <td>${escapeHTML(signLabel(row))}</td>
                <td>${escapeHTML(row.degree_str)}</td>
                <td>${escapeHTML(row.house_from_karakamsa)}</td>
                <td>${escapeHTML(row.house_class)}</td>
            </tr>
        `).join('')
        : '';
    const strongestArgala = Array.isArray(argalaSummary.strongest_sources)
        ? argalaSummary.strongest_sources[0]
        : null;
    const supportFactors = Array.isArray(karakamsa.support_factors)
        ? karakamsa.support_factors
        : [];
    const challengeFactors = Array.isArray(karakamsa.challenge_factors)
        ? karakamsa.challenge_factors
        : [];
    const technicalRows = [
        [
            'Karakamsa destek',
            supportFactors.slice(0, 4).map(row => `${row.planet} Ev ${row.house_from_karakamsa}`).join(', ') || '-',
            `Toplam ${supportFactors.length} destek faktörü`,
        ],
        [
            'Karakamsa zorluk',
            challengeFactors.slice(0, 4).map(row => `${row.planet} Ev ${row.house_from_karakamsa}`).join(', ') || '-',
            `Toplam ${challengeFactors.length} zorlayıcı faktör`,
        ],
        [
            'Argala lideri',
            strongestArgala ? `${strongestArgala.source} (${strongestArgala.net_score})` : '-',
            strongestArgala ? `Güç ${strongestArgala.strength}` : '-',
        ],
        [
            'Swamsha',
            signLabel(swamsha.swamsha_lagna),
            `${Array.isArray(swamsha.d9_planets_from_swamsha) ? swamsha.d9_planets_from_swamsha.length : 0} D9 gezegen kaydı`,
        ],
    ].map(row => `
        <tr>
            <td>${escapeHTML(row[0])}</td>
            <td>${escapeHTML(row[1])}</td>
            <td>${escapeHTML(row[2])}</td>
        </tr>
    `).join('');

    container.innerHTML = `
        <div class="layer-summary-strip">
            <div><span>Karakamsa</span><strong>${escapeHTML(signLabel(karakamsa.karakamsa_lagna))}</strong></div>
            <div><span>Atmakaraka</span><strong>${escapeHTML(karakamsa.atmakaraka || '-')}</strong></div>
            <div><span>Swamsha</span><strong>${escapeHTML(signLabel(swamsha.swamsha_lagna))}</strong></div>
            <div><span>Upapada</span><strong>${escapeHTML(signLabel(arudha.upapada && arudha.upapada.pada))}</strong></div>
        </div>
        <div class="layer-summary-strip">
            <div><span>UL Lord</span><strong>${escapeHTML(upapadaDetail.upapada_lord ? upapadaDetail.upapada_lord.planet : '-')}</strong></div>
            <div><span>UL Occupants</span><strong>${escapeHTML((upapadaDetail.occupants || []).join(', ') || '-')}</strong></div>
            <div><span>2nd From UL</span><strong>${escapeHTML(signLabel(upapadaDetail.second_from_upapada))}</strong></div>
            <div><span>2nd Lord</span><strong>${escapeHTML(upapadaDetail.second_from_upapada ? upapadaDetail.second_from_upapada.lord : '-')}</strong></div>
        </div>
        <div class="layer-summary-strip">
            <div><span>Chara sistem</span><strong>${escapeHTML(chara.system || '-')}</strong></div>
            <div><span>Argala lideri</span><strong>${escapeHTML(strongestArgala ? strongestArgala.source : '-')}</strong></div>
            <div><span>Destek faktörü</span><strong>${escapeHTML(supportFactors.length)}</strong></div>
            <div><span>Zorluk faktörü</span><strong>${escapeHTML(challengeFactors.length)}</strong></div>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Rol</th><th>Gezegen</th><th>Burç</th><th>Derece</th><th>Nakshatra</th></tr></thead>
                <tbody>${charaRows}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>D9 Gezegen</th><th>D9 Burç</th><th>Derece</th><th>Karakamsa'dan Ev</th><th>Sınıf</th></tr></thead>
                <tbody>${karakamsaRows || '<tr><td colspan="5">Karakamsa teknik detayı yok</td></tr>'}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Pada</th><th>Burç</th><th>Lord</th><th>Skor</th></tr></thead>
                <tbody>${padaRows || '<tr><td colspan="4">Arudha verisi yok</td></tr>'}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Argala Kaynak</th><th>Burç</th><th>Aktif</th><th>Engelli</th><th>Net</th><th>Güç</th></tr></thead>
                <tbody>${argalaRows || '<tr><td colspan="6">Argala verisi yok</td></tr>'}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Teknik Alan</th><th>Öne Çıkanlar</th><th>Not</th></tr></thead>
                <tbody>${technicalRows}</tbody>
            </table>
        </div>
    `;
}

function renderKp(data) {
    const container = document.getElementById('kp-content');
    if (!container) return;
    const kp = data.kp;
    if (!kp || !Array.isArray(kp.cusps)) {
        container.innerHTML = '<p class="layer-empty">KP verisi yok.</p>';
        return;
    }

    const planetSignificators = kp.significators && Array.isArray(kp.significators.planet_significators)
        ? kp.significators.planet_significators
        : [];
    const technicalKpNote = (row) => {
        const ranked = Array.isArray(row.ranked_houses) ? row.ranked_houses.slice(0, 3) : [];
        const topHouses = ranked.map(item => `Ev ${item.house} (${item.score})`).join(', ') || '-';
        const leadSource = ranked[0] && Array.isArray(ranked[0].sources) ? ranked[0].sources[0] : null;
        return `Star ${row.star_lord || '-'}, Sub ${row.sub_lord || '-'}, Sub-Sub ${row.sub_sub_lord || '-'}; baskın evler ${topHouses}; ilk kaynak ${leadSource || '-'}.`;
    };

    const cuspRows = kp.cusps.slice(0, 12).map(cusp => `
        <tr>
            <td>${escapeHTML(cusp.house)}</td>
            <td>${escapeHTML(signLabel(cusp))}</td>
            <td>${escapeHTML(cusp.nakshatra_lord)}</td>
            <td>${escapeHTML(cusp.sub_lord)}</td>
            <td>${escapeHTML(cusp.sub_sub_lord)}</td>
        </tr>
    `).join('');
    const planetRows = kp.planets.map(planet => `
        <tr>
            <td>${escapeHTML(planet.planet)}</td>
            <td>${escapeHTML(signLabel(planet))}</td>
            <td>${escapeHTML(planet.nakshatra_lord)}</td>
            <td>${escapeHTML(planet.sub_lord)}</td>
            <td>${escapeHTML(planet.sub_sub_lord)}</td>
        </tr>
    `).join('');
    const ruling = kp.ruling_planets && Array.isArray(kp.ruling_planets.entries)
        ? kp.ruling_planets.entries
        : [];
    const rulingRows = ruling.map(entry => `
        <tr>
            <td>${escapeHTML(entry.role)}</td>
            <td>${escapeHTML(entry.planet)}</td>
        </tr>
    `).join('');
    const uniqueRuling = kp.ruling_planets && Array.isArray(kp.ruling_planets.unique_planets)
        ? kp.ruling_planets.unique_planets
        : [];
    const houseSignificators = kp.significators && kp.significators.house_significators
        ? kp.significators.house_significators
        : {};
    const houseRows = Object.entries(houseSignificators).map(([house, rows]) => {
        const planets = (rows || []).slice(0, 5).map(row => `${row.planet} (${row.score})`).join(', ');
        return `<tr>
            <td>${escapeHTML(house)}</td>
            <td>${escapeHTML(planets || '-')}</td>
        </tr>`;
    }).join('');
    const planetSignificatorRows = planetSignificators.map(row => {
        const topHouses = (row.ranked_houses || []).slice(0, 4).map(item => `Ev ${item.house} (${item.score})`).join(', ');
        return `
            <tr>
                <td>${escapeHTML(row.planet)}</td>
                <td>${escapeHTML(row.star_lord || '-')}</td>
                <td>${escapeHTML(row.sub_lord || '-')}</td>
                <td>${escapeHTML(row.sub_sub_lord || '-')}</td>
                <td>${escapeHTML(topHouses || '-')}</td>
                <td>${escapeHTML(technicalKpNote(row))}</td>
            </tr>
        `;
    }).join('');
    const strongestHouseEntry = Object.entries(houseSignificators)
        .map(([house, rows]) => ({
            house,
            count: Array.isArray(rows) ? rows.length : 0,
            top: Array.isArray(rows) && rows[0] ? `${rows[0].planet} (${rows[0].score})` : '-',
        }))
        .sort((a, b) => b.count - a.count)[0];
    const cuspMode = kp.cusp_status === 'implemented_placidus' ? 'Placidus' : 'Whole sign fallback';

    container.innerHTML = `
        ${renderLayerMeta(kp)}
        <div class="layer-summary-strip">
            <div><span>Cusp modu</span><strong>${escapeHTML(cuspMode)}</strong></div>
            <div><span>Ruling planets</span><strong>${escapeHTML(uniqueRuling.join(', ') || '-')}</strong></div>
            <div><span>Gezegen satırı</span><strong>${escapeHTML(kp.planets.length)}</strong></div>
            <div><span>Ev satırı</span><strong>${escapeHTML(kp.cusps.length)}</strong></div>
        </div>
        <div class="layer-summary-strip">
            <div><span>En dolu ev</span><strong>${escapeHTML(strongestHouseEntry ? `Ev ${strongestHouseEntry.house}` : '-')}</strong></div>
            <div><span>Significator sayısı</span><strong>${escapeHTML(strongestHouseEntry ? strongestHouseEntry.count : '-')}</strong></div>
            <div><span>İlk gezegen</span><strong>${escapeHTML(strongestHouseEntry ? strongestHouseEntry.top : '-')}</strong></div>
            <div><span>Ruling rol</span><strong>${escapeHTML(ruling.length)}</strong></div>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Ev</th><th>Cusp</th><th>Star Lord</th><th>Sub Lord</th><th>Sub-Sub Lord</th></tr></thead>
                <tbody>${cuspRows}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Gezegen</th><th>Burç</th><th>Star Lord</th><th>Sub Lord</th><th>Sub-Sub Lord</th></tr></thead>
                <tbody>${planetRows}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Ev</th><th>Significator Gezegenler</th></tr></thead>
                <tbody>${houseRows}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Gezegen</th><th>Star</th><th>Sub</th><th>Sub-Sub</th><th>İlk Evler</th><th>Teknik Not</th></tr></thead>
                <tbody>${planetSignificatorRows || '<tr><td colspan="6">Gezegen significator tablosu yok</td></tr>'}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Ruling Planet Rolü</th><th>Gezegen</th></tr></thead>
                <tbody>${rulingRows || '<tr><td colspan="2">Ruling planets yok</td></tr>'}</tbody>
            </table>
        </div>
    `;
}

function transitNakshatraName(item) {
    const nakshatra = item && item.nakshatra ? item.nakshatra : {};
    if (!nakshatra.name) return '-';
    const lord = nakshatra.lord ? ` (${nakshatra.lord})` : '';
    return `${nakshatra.name}${lord}`;
}

function transitNakshatraPada(item) {
    const nakshatra = item && item.nakshatra ? item.nakshatra : {};
    return nakshatra.pada || '-';
}

function panchangaTransitRows(data) {
    const panchanga = data.panchanga || {};
    const tithi = panchanga.tithi || {};
    const paksha = panchanga.paksha || {};
    const vara = panchanga.vara || {};
    const yoga = panchanga.yoga || {};
    const karana = panchanga.karana || {};
    const moonNakshatra = panchanga.moon_nakshatra || {};
    return [
        ['Tithi', tithi.name || '', tithi.number || '', tithi.paksha_tithi || '', paksha.name || '', tithi.remaining_degrees || ''],
        ['Paksha', paksha.name || '', paksha.phase || '', '', '', ''],
        ['Vara', vara.name || '', vara.weekday_index || '', '', vara.sanskrit || '', ''],
        ['Yoga', yoga.name || '', yoga.number || '', '', '', yoga.remaining_degrees || ''],
        ['Karana', karana.name || '', karana.number || '', '', '', karana.remaining_degrees || ''],
        ['Ay Nakshatra', moonNakshatra.name || '', moonNakshatra.number || '', moonNakshatra.pada || '', moonNakshatra.lord || '', moonNakshatra.degree_str || ''],
    ];
}

function transitBavSupportLevel(bindus) {
    if (bindus === null || bindus === undefined || bindus === '') return 'not_available';
    const value = Number(bindus);
    if (Number.isNaN(value)) return 'not_available';
    if (value >= 6) return 'high_support';
    if (value === 5) return 'moderate_support';
    if (value >= 3) return 'low_support';
    return 'critical_low';
}

function transitAshtakavargaScore(data, planet) {
    const rows = data.ashtakavarga && data.ashtakavarga.transit_scoring
        ? data.ashtakavarga.transit_scoring.rows || []
        : [];
    const score = rows.find(row => row.planet === planet.name) || {};
    return {
        sav: score.sarva_bindus ?? '',
        savLevel: score.sarva_support_level || '',
        bav: score.planet_bhinna_bindus ?? '',
        bavLevel: score.planet_bhinna_available ? transitBavSupportLevel(score.planet_bhinna_bindus) : 'not_available',
    };
}

function transitGuideMarkdownLines() {
    return [
        '## Transit Veri Paketi Kılavuzu',
        '',
        '### AstroGPT Okuma Talimatı',
        '',
        '- Bu dosya hesaplama kaynağıdır; AstroGPT ek transit, panchanga, dasha veya gezegen konumu hesaplamaz.',
        '- Kullanıcı bir tarih aralığı verirse yalnızca o aralıktaki Günlük Özet satırları ve Gün Detayları kullanılmalıdır.',
        '- Analize başlamadan önce bu dosyanın Dönem Özeti içindeki gerçek başlangıç ve bitiş tarihini açıkça yaz.',
        '- İstenen dönem dosya aralığından farklıysa yalnız ortak tarih aralığını analiz et ve kapsanmayan başlangıç/bitiş günlerini belirt.',
        '- İstenen dönemle dosya aralığı kesişmiyorsa analizi durdur; başka transit dosyasından veya konu paketinden transit konumu aktarma.',
        '- Analiz dili ilişki/iş/para/sağlık gibi konuya göre değişebilir; fakat veri kullanım sırası değişmez.',
        '',
        '### Kullanım Sırası',
        '',
        "1. Önce Dönem Özeti'nden paket türünü, tarih aralığını, kayıt sayısını, transit saatini ve saat dilimini oku.",
        '2. İstenen dönemle dosya tarih aralığını karşılaştır; ortak aralığı ve kapsanmayan günleri belirle.',
        "3. Yalnız ortak tarih aralığı için Günlük Özet Tablosu'ndaki satırları seç.",
        '4. Ana aktivasyon için Aktif Dasha yolunu kullan: maha, antara, pratyantar ve varsa sookshma.',
        '5. Gün Detayları içindeki Panchanga tablosunu destekleyici günlük bağlam olarak kullan: tithi, paksha, vara, yoga, karana, Ay nakshatra ve Ay pada.',
        "6. Ay verisini günlük zamanlama ve duygu/olay tetikleyicisi olarak kullan: Ay burcu, derece, nakshatra, pada, Lagna'dan ev ve natal Ay'dan ev.",
        '7. Transit Gezegen Snapshot tablosunda özellikle Satürn, Jüpiter, Rahu/Ketu, Mars ve Venüs konumlarını Lagna ve natal Ay referansıyla oku.',
        '8. Transit Gezegen Snapshot içindeki SAV ve BAV skorlarını kontrol et; düşük SAV/BAV varsa transit faydası zayıflamış teknik destekle okunur.',
        '9. Dasha Transit Kesişimi tablosunda aktif dasha lordlarının transit konumu ve natal temas sayıları ana kanıt olarak kullanılır.',
        '10. Natal Temasları tablosunda derece orb temasları aynı burç temaslarından daha güçlü kabul edilir.',
        '11. Özel Kontroller tablosu Sade Sati, Ashtama Shani, Kantaka Shani, Jüpiter desteği ve Rahu/Ketu ekseni için kontrol katmanıdır.',
        '',
        '### Hüküm Kuralları',
        '',
        '- Tek göstergeyle kesin hüküm verme; dasha, transit temas, özel kontrol ve Panchanga birlikte destekliyorsa daha net konuş.',
        '- Dasha ana dönem aktivasyonudur; transitler bu aktivasyonu zamanlar ve görünür hale getirir.',
        '- Panchanga ve Ay nakshatra/pada günlük kalite ve zamanlama verir; tek başına evlilik, ayrılık, hastalık, iş değişimi gibi kesin olay hükmü üretmez.',
        '- Satürn/Jüpiter/Rahu-Ketu gibi yavaş göstergeler aylık ve 3 aylık yorumda; Ay ve Panchanga günlük yorumda daha ağırlıklıdır.',
        '- Bu paket hazır bir en güçlü pencere sıralaması üretmez.',
        '- Burç, retro veya dasha değişim tarihlerini otomatik olarak pencere başlangıcı ya da bitişi sayma.',
        '- Kullanıcı belirli sayıda pencere isterse çoklu günlük kanıtla tanımlı bir sıralama yokken pencere veya güç etiketi uydurma; güvenilir ayrım üretilemiyorsa bunu açıkça belirt.',
        '- Eksik veri varsa bunu açıkça söyle; dosyada olmayan klasik kuralı veya hesaplamayı uydurma.',
        '',
        '### Paket Türü Talimatı',
        '',
        '- Günlük analizde ilgili günün tüm Gün Detayları kullanılır.',
        '- Haftalık analizde 7 günlük kayıtlar taranır; tekrar eden dasha/transit temaları ve sivrilen günler özetlenir.',
        '- Aylık analizde ayın tüm günlük kayıtları taranır; tema kümeleri, kritik günler ve rahatlatıcı günler ayrılır.',
        '- 3 aylık analizde her gün taranır; ay ay ana aktivasyonlar, yoğunlaşan dönemler ve karar eşikleri çıkarılır.',
        '- 6 aylık analizde tüm günlük kayıtlar taranır; aylık kümeler karşılaştırılır, fakat hazır sıralama yoksa belirli sayıda pencere ilan edilmez.',
        '- Özel tarih aralığı analizinde yalnız seçili aralığın günlük kayıtları kullanılır; teknik değişim tarihleri tek başına pencere sınırı kabul edilmez.',
    ];
}

function renderTransits(data) {
    const container = document.getElementById('transits-content');
    if (!container) return;
    const transits = data.transits;
    if (!transits || !Array.isArray(transits.planets)) {
        container.innerHTML = '<p class="layer-empty">Transit verisi yok.</p>';
        return;
    }

    const bavSupportLabel = (level) => ({
        high_support: 'Yüksek destek',
        moderate_support: 'Orta destek',
        low_support: 'Düşük destek',
        critical_low: 'Kritik düşük',
        not_available: '-',
    }[level] || level || '-');

    const transitTechnicalNote = (item) => {
        const av = transitAshtakavargaScore(data, item);
        const natalInSign = Array.isArray(item.natal_planets_in_sign) && item.natal_planets_in_sign.length
            ? item.natal_planets_in_sign.join(', ')
            : 'yok';
        return `Lagna’dan ${item.house_from_natal_lagna}, Ay’dan ${item.house_from_natal_moon}; SAV ${av.sav || '-'} (${av.savLevel || '-'}), BAV ${av.bav || '-'} (${bavSupportLabel(av.bavLevel)}), aynı burç natal temas ${natalInSign}.`;
    };

    const rows = transits.planets.map(item => {
        const av = transitAshtakavargaScore(data, item);
        return `
            <tr>
                <td>${escapeHTML(item.name)}</td>
                <td>${escapeHTML(signLabel(item))}</td>
                <td>${escapeHTML(item.degree_str || '-')}</td>
                <td>${escapeHTML(transitNakshatraName(item))}</td>
                <td>${escapeHTML(transitNakshatraPada(item))}</td>
                <td>${escapeHTML(item.house_from_natal_lagna)}</td>
                <td>${escapeHTML(item.house_from_natal_moon)}</td>
                <td>${escapeHTML(av.sav || '-')}</td>
                <td>${escapeHTML(av.savLevel || '-')}</td>
                <td>${escapeHTML(av.bav || '-')}</td>
                <td>${escapeHTML(bavSupportLabel(av.bavLevel))}</td>
            </tr>
        `;
    }).join('');
    const technicalRows = transits.planets.map(item => `
        <tr>
            <td>${escapeHTML(item.name)}</td>
            <td>${escapeHTML(item.motion ? item.motion.speed_status || '-' : '-')}</td>
            <td>${escapeHTML(transitTechnicalNote(item))}</td>
        </tr>
    `).join('');
    const panchangaRows = panchangaTransitRows(data).map(row => `
        <tr>${row.map(cell => `<td>${escapeHTML(cell || '-')}</td>`).join('')}</tr>
    `).join('');
    const dashaRows = transits.dasha_cross_reference && Array.isArray(transits.dasha_cross_reference.rows)
        ? transits.dasha_cross_reference.rows.map(row => `
            <tr>
                <td>${escapeHTML(row.level)}</td>
                <td>${escapeHTML(row.lord)}</td>
                <td>${escapeHTML(signLabel(row.transit))}</td>
                <td>${escapeHTML(row.transit.house_from_natal_lagna || '-')}</td>
                <td>${escapeHTML(row.transit.house_from_natal_moon || '-')}</td>
                <td>${escapeHTML((row.contacts_as_transit || []).length)}</td>
                <td>${escapeHTML((row.contacts_to_natal_lord || []).length)}</td>
            </tr>
        `).join('')
        : '';
    const specialChecks = transits.special_checks || {};
    const saturn = specialChecks.saturn || {};
    const jupiter = specialChecks.jupiter || {};
    const nodes = specialChecks.nodes || {};
    const natalContacts = Array.isArray(transits.natal_contacts) ? transits.natal_contacts : [];
    const topContacts = natalContacts.slice(0, 8).map(contact => `
        <tr>
            <td>${escapeHTML(contact.transit_planet)}</td>
            <td>${escapeHTML(contact.natal_planet)}</td>
            <td>${escapeHTML(contact.contact_type)}</td>
            <td>${escapeHTML(contact.orb)}</td>
            <td>${escapeHTML(contact.sign)}</td>
            <td>${escapeHTML(contact.house_from_lagna)}</td>
            <td>${escapeHTML(contact.house_from_moon)}</td>
        </tr>
    `).join('');
    const dashaActivePath = transits.dasha_cross_reference && Array.isArray(transits.dasha_cross_reference.active_path)
        ? transits.dasha_cross_reference.active_path.join(' > ')
        : '-';

    container.innerHTML = `
        ${renderLayerMeta(transits)}
        <div class="layer-summary-strip">
            <div><span>Transit Modu</span><strong>${escapeHTML(transits.reference_mode || '-')}</strong></div>
            <div><span>Referans UTC</span><strong>${escapeHTML(transits.reference_datetime_utc || '-')}</strong></div>
            <div><span>Seçilen Tarih</span><strong>${escapeHTML(transits.requested_date || 'anlık')}</strong></div>
            <div><span>UTC Farkı</span><strong>${escapeHTML(transits.requested_tz_offset)}</strong></div>
        </div>
        <div class="layer-summary-strip">
            <div><span>Dasha yolu</span><strong>${escapeHTML(dashaActivePath)}</strong></div>
            <div><span>Natal temas</span><strong>${escapeHTML(natalContacts.length)}</strong></div>
            <div><span>Jüpiter desteği</span><strong>${escapeHTML((jupiter.from_moon && jupiter.from_moon.traditionally_supportive) ? 'Ay destekli' : 'nötr/zayıf')}</strong></div>
            <div><span>Satürn baskısı</span><strong>${escapeHTML((saturn.sade_sati && saturn.sade_sati.is_active) ? 'Sade Sati' : (saturn.ashtama_shani && saturn.ashtama_shani.is_active) ? 'Ashtama' : (saturn.kantaka_shani && saturn.kantaka_shani.is_active) ? 'Kantaka' : 'özel baskı yok')}</strong></div>
        </div>
        <div class="layer-summary-strip">
            <div><span>Satürn Ay’dan</span><strong>${escapeHTML((saturn.sade_sati || {}).house_from_moon ?? '-')}</strong></div>
            <div><span>Jüpiter Ay’dan</span><strong>${escapeHTML((jupiter.from_moon || {}).house ?? '-')}</strong></div>
            <div><span>Rahu Lagna’dan</span><strong>${escapeHTML((((nodes.from_lagna || {}).rahu || {}).house_from_reference) ?? '-')}</strong></div>
            <div><span>Ketu Lagna’dan</span><strong>${escapeHTML((((nodes.from_lagna || {}).ketu || {}).house_from_reference) ?? '-')}</strong></div>
        </div>
        <div class="layer-note">
            <strong>Transit Veri Paketi Kılavuzu:</strong>
            GPT bu pakette önce dönem aralığını ve ilgili gün satırlarını seçer; sonra aktif dasha,
            Panchanga, Ay nakshatra/pada, transit snapshot, Ashtakavarga SAV/BAV, dasha-transit kesişimi,
            natal temaslar ve özel kontrolleri birlikte okur. Panchanga ve Ay tek başına kesin olay hükmü değildir;
            dasha ana aktivasyon, transitler zamanlama katmanıdır.
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Anga</th><th>Ad</th><th>No/Faz</th><th>Pada/Index</th><th>Ek</th><th>Kalan/Der.</th></tr></thead>
                <tbody>${panchangaRows}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Gezegen</th><th>Burç</th><th>Derece</th><th>Nakshatra</th><th>Pada</th><th>Lagna’dan</th><th>Ay’dan</th><th>SAV</th><th>SAV Seviye</th><th>BAV</th><th>BAV Seviye</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Dasha</th><th>Lord</th><th>Transit</th><th>Lagna’dan</th><th>Ay’dan</th><th>Transit Temas</th><th>Natal Lord Temas</th></tr></thead>
                <tbody>${dashaRows || '<tr><td colspan="7">Dasha + transit çapraz verisi yok</td></tr>'}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Gezegen</th><th>Hareket</th><th>Teknik Not</th></tr></thead>
                <tbody>${technicalRows}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Transit</th><th>Natal</th><th>Tip</th><th>Orb</th><th>Burç</th><th>Lagna’dan</th><th>Ay’dan</th></tr></thead>
                <tbody>${topContacts || '<tr><td colspan="7">Natal temas verisi yok</td></tr>'}</tbody>
            </table>
        </div>
    `;
}

function generateTransitCopyPackage(data) {
    const person = lastPersonInfo || {};
    const birth = data.birth || data.birth_info || {};
    const transits = data.transits || {};
    const dashaRows = transits.dasha_cross_reference && Array.isArray(transits.dasha_cross_reference.rows)
        ? transits.dasha_cross_reference.rows.map(row => [
            row.level,
            row.lord,
            markdownSign(row.transit),
            row.transit ? row.transit.house_from_natal_lagna || '' : '',
            row.transit ? row.transit.house_from_natal_moon || '' : '',
            (row.contacts_as_transit || []).length,
            (row.contacts_to_natal_lord || []).length,
        ])
        : [];
    const planetRows = Array.isArray(transits.planets)
        ? transits.planets.map(planet => {
            const av = transitAshtakavargaScore(data, planet);
            return [
                planet.name,
                markdownSign(planet),
                planet.degree_str,
                planet.nakshatra ? `${planet.nakshatra.name}${planet.nakshatra.lord ? ` (${planet.nakshatra.lord})` : ''}` : '',
                planet.nakshatra ? planet.nakshatra.pada || '' : '',
                planet.house_from_natal_lagna,
                planet.house_from_natal_moon,
                av.sav,
                av.savLevel,
                av.bav,
                av.bavLevel,
                planet.motion ? planet.motion.speed_status : '',
                (planet.natal_planets_in_sign || []).join(', '),
            ];
        })
        : [];
    const contactRows = Array.isArray(transits.natal_contacts)
        ? transits.natal_contacts.slice(0, 30).map(contact => [
            contact.transit_planet,
            contact.natal_planet,
            contact.contact_type,
            contact.orb,
            contact.sign,
            contact.house_from_lagna,
            contact.house_from_moon,
        ])
        : [];
    const saturn = transits.special_checks ? transits.special_checks.saturn || {} : {};
    const jupiter = transits.special_checks ? transits.special_checks.jupiter || {} : {};
    const nodes = transits.special_checks ? transits.special_checks.nodes || {} : {};

    return [
        `# ${person.name || birth.person?.name || 'Danışan'} Transit Teknik Paketi`,
        '',
        ...transitGuideMarkdownLines(),
        '',
        '## Referans',
        '',
        `- Doğum: ${birth.date || ''} ${birth.time || ''}`,
        `- Yer: ${birth.place || ''}`,
        `- Transit modu: ${transits.reference_mode || ''}`,
        `- Referans UTC: ${transits.reference_datetime_utc || ''}`,
        `- Seçilen tarih: ${transits.requested_date || 'anlık'}`,
        `- Seçilen saat: ${transits.requested_time || ''}`,
        `- Method: ${transits.method || ''}`,
        `- Source rule: ${transits.source_rule || ''}`,
        `- Assumptions: ${(transits.assumptions || []).join(', ')}`,
        `- Excluded rules: ${(transits.excluded_rules || []).join(', ')}`,
        '',
        '## Panchanga',
        '',
        markdownTable(['Anga', 'Ad', 'No/Faz', 'Pada/Index', 'Ek', 'Kalan/Der.'], panchangaTransitRows(data)),
        '',
        '## Özel Gochar Kontrolleri',
        '',
        `- Sade Sati: ${saturn.sade_sati ? saturn.sade_sati.is_active : ''} / ${saturn.sade_sati ? saturn.sade_sati.phase || '' : ''}`,
        `- Ashtama Shani: ${saturn.ashtama_shani ? saturn.ashtama_shani.is_active : ''}`,
        `- Kantaka Shani: ${saturn.kantaka_shani ? saturn.kantaka_shani.is_active : ''}`,
        `- Jupiter Ay’dan: ${jupiter.from_moon ? jupiter.from_moon.house || '' : ''}`,
        `- Jupiter Lagna’dan: ${jupiter.from_lagna ? jupiter.from_lagna.house || '' : ''}`,
        `- Rahu/Ketu Ay’dan: ${nodes.from_moon ? `${nodes.from_moon.rahu?.house_from_reference || ''}/${nodes.from_moon.ketu?.house_from_reference || ''}` : ''}`,
        `- Rahu/Ketu Lagna’dan: ${nodes.from_lagna ? `${nodes.from_lagna.rahu?.house_from_reference || ''}/${nodes.from_lagna.ketu?.house_from_reference || ''}` : ''}`,
        '',
        '## Transit Gezegenleri',
        '',
        markdownTable(['Gezegen', 'Burç', 'Derece', 'Nakshatra', 'Pada', 'Lagna’dan', 'Ay’dan', 'SAV', 'SAV Seviye', 'BAV', 'BAV Seviye', 'Hız', 'Aynı Burç Natal'], planetRows),
        '',
        '## Aktif Dasha + Transit Çaprazı',
        '',
        markdownTable(['Dasha', 'Lord', 'Transit Burç', 'Lagna’dan', 'Ay’dan', 'Transit Temas', 'Natal Lord Temas'], dashaRows),
        '',
        '## Natal Temaslar',
        '',
        markdownTable(['Transit', 'Natal', 'Tip', 'Orb', 'Burç', 'Lagna’dan', 'Ay’dan'], contactRows),
        '',
        '## Teknik Not',
        '',
        '- Bu paket transit hesap verisidir; yorum metni değildir.',
        '- Transit katmanı aynı burç temaslarını ve 3 derece orb içindeki derece temaslarını listeler.',
    ].join('\n');
}

async function copyTransitPackage() {
    if (!lastChartData || !lastChartData.transits) {
        setVaultStatus('Önce harita hesapla.', 'error');
        return;
    }
    try {
        await navigator.clipboard.writeText(generateTransitCopyPackage(lastChartData));
        setVaultStatus('Transit paketi panoya alındı.', 'success');
    } catch (err) {
        setVaultStatus('Kopyalama tarayıcı tarafından engellendi; metni elle seçebilirsin.', 'error');
    }
}

function renderVarshaphala(data) {
    const container = document.getElementById('varshaphala-content');
    if (!container) return;
    const layer = data.varshaphala;
    if (!layer || !layer.year) {
        container.innerHTML = '<p class="layer-empty">Varshaphala verisi yok.</p>';
        return;
    }

    const year = layer.year || {};
    const muntha = layer.muntha || {};
    const selectedLord = layer.year_lord ? layer.year_lord.selected : null;
    const activeMudda = layer.mudda_dasha ? layer.mudda_dasha.active : null;
    const planetRows = Array.isArray(layer.planets)
        ? layer.planets.map(planet => `
            <tr>
                <td>${escapeHTML(planet.name)}</td>
                <td>${escapeHTML(signLabel(planet))}</td>
                <td>${escapeHTML(planet.degree_str || '-')}</td>
                <td>${escapeHTML(planet.house || '-')}</td>
                <td>${escapeHTML(planet.natal_house || '-')}</td>
            </tr>
        `).join('')
        : '';
    const dashaRows = layer.mudda_dasha && Array.isArray(layer.mudda_dasha.periods)
        ? layer.mudda_dasha.periods.map(period => `
            <tr>
                <td>${escapeHTML(period.lord)}</td>
                <td>${escapeHTML(period.duration_days)}</td>
                <td>${escapeHTML(period.start_utc || '-')}</td>
                <td>${escapeHTML(period.end_utc || '-')}</td>
                <td>${period.is_active ? 'aktif' : ''}</td>
            </tr>
        `).join('')
        : '';
    const lordRows = layer.year_lord && Array.isArray(layer.year_lord.candidates)
        ? layer.year_lord.candidates.map(candidate => `
            <tr>
                <td>${escapeHTML(candidate.role)}</td>
                <td>${escapeHTML(candidate.planet)}</td>
                <td>${escapeHTML(candidate.score)}</td>
                <td>${escapeHTML(candidate.annual_house || '-')}</td>
                <td>${escapeHTML((candidate.strength_factors || []).join(', ') || '-')}</td>
            </tr>
        `).join('')
        : '';

    container.innerHTML = `
        ${renderLayerMeta(layer)}
        <div class="layer-summary-strip">
            <div><span>Varsha Başlangıcı</span><strong>${escapeHTML(year.start_local || '-')}</strong></div>
            <div><span>Tamamlanan Yaş</span><strong>${escapeHTML(year.completed_years)}</strong></div>
            <div><span>Varsha Lagna</span><strong>${escapeHTML(signLabel(layer.varsha_lagna))}</strong></div>
            <div><span>Muntha</span><strong>${escapeHTML(signLabel(muntha))} / ${escapeHTML(muntha.house_from_varsha_lagna || '-')}</strong></div>
            <div><span>Yıl Lordu</span><strong>${escapeHTML(selectedLord ? selectedLord.planet : '-')}</strong></div>
            <div><span>Aktif Mudda</span><strong>${escapeHTML(activeMudda ? activeMudda.lord : '-')}</strong></div>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Yıl Lordu Rolü</th><th>Gezegen</th><th>Skor</th><th>Yıllık Ev</th><th>Faktör</th></tr></thead>
                <tbody>${lordRows || '<tr><td colspan="5">Yıl lordu adayı yok</td></tr>'}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Gezegen</th><th>Varsha Burç</th><th>Derece</th><th>Yıllık Ev</th><th>Natal Ev</th></tr></thead>
                <tbody>${planetRows || '<tr><td colspan="5">Varsha gezegen verisi yok</td></tr>'}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Mudda Lord</th><th>Gün</th><th>Başlangıç UTC</th><th>Bitiş UTC</th><th></th></tr></thead>
                <tbody>${dashaRows || '<tr><td colspan="5">Mudda dasha verisi yok</td></tr>'}</tbody>
            </table>
        </div>
    `;
}

function renderAdvancedLayers(data) {
    renderAshtakavarga(data);
    renderShadbala(data);
    renderDoshas(data);
    renderJaiminiDetails(data);
    renderKp(data);
    renderVarshaphala(data);
    renderTransits(data);
}

function markdownValue(value) {
    if (value === null || value === undefined) return '';
    return String(value).replace(/\|/g, '\\|').replace(/\n/g, ' ');
}

function markdownTable(headers, rows) {
    const header = `| ${headers.join(' | ')} |`;
    const separator = `| ${headers.map(() => '---').join(' | ')} |`;
    const body = rows.map(row => `| ${row.map(markdownValue).join(' | ')} |`);
    return [header, separator, ...body].join('\n');
}

function markdownSign(item) {
    if (!item) return '';
    if (item.sign_tr && item.sign) return `${item.sign_tr} (${item.sign})`;
    return item.sign_tr || item.sign || '';
}

function birthTimeConfidenceForForm() {
    const status = document.getElementById('birth-time-status');
    if (status && ['known', 'unknown', 'rectified'].includes(status.value)) {
        return status.value;
    }
    const hour = Number(document.getElementById('hour').value || 0);
    const minute = Number(document.getElementById('minute').value || 0);
    const second = Number(document.getElementById('second').value || 0);
    return hour === 0 && minute === 0 && second === 0 ? 'unknown' : 'known';
}

function rectificationSourceForForm() {
    return birthTimeConfidenceForForm() === 'rectified'
        ? 'external_astrolog_or_user_confirmed'
        : undefined;
}

function invalidateRectifiedBirthTime() {
    const status = document.getElementById('birth-time-status');
    if (status) {
        status.value = 'unknown';
    }
}

function hhmmFromMinutes(totalMinutes) {
    const bounded = Math.max(0, Math.min(1439, totalMinutes));
    const hour = Math.floor(bounded / 60);
    const minute = bounded % 60;
    return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}:00`;
}

function activeDashaRows(data) {
    const active = data.dashas && data.dashas.vimshottari
        ? (data.dashas.vimshottari.current_active || data.dashas.vimshottari.active || {})
        : {};
    return ['maha', 'antara', 'pratyantar', 'sookshma']
        .filter(level => active[level])
        .map(level => {
            const period = active[level];
            return [level, period.lord, period.start, period.end, period.effective_years || ''];
        });
}

function expertVargaRows(data, division) {
    const varga = data.vargas && data.vargas[division];
    if (!varga) return [];
    const rows = [];
    if (varga.lagna) {
        rows.push(['Lagna', markdownSign(varga.lagna), varga.lagna.degree_str || '']);
    }
    return rows.concat((varga.planets || []).map(planet => [
        planet.name,
        markdownSign(planet),
        planet.degree_str || '',
    ]));
}

function expertSavRows(data) {
    const rows = data.ashtakavarga && data.ashtakavarga.sarva
        ? (data.ashtakavarga.sarva.by_sign || [])
        : [];
    return rows
        .slice()
        .sort((a, b) => (a.house || 99) - (b.house || 99))
        .map(row => [row.house, markdownSign(row), row.bindus]);
}

function expertBavHeaders(data) {
    const ashtakavarga = data.ashtakavarga || {};
    if (ashtakavarga.ruleset && Array.isArray(ashtakavarga.ruleset.target_planets)) {
        return ashtakavarga.ruleset.target_planets;
    }
    return Object.keys(ashtakavarga.bhinna || {});
}

function expertBavRows(data) {
    const ashtakavarga = data.ashtakavarga || {};
    const savRows = ashtakavarga.sarva ? (ashtakavarga.sarva.by_sign || []) : [];
    const planets = expertBavHeaders(data);
    return savRows
        .slice()
        .sort((a, b) => (a.house || 99) - (b.house || 99))
        .map(savRow => {
            const row = [savRow.house, markdownSign(savRow)];
            planets.forEach(planet => {
                const bavRow = ((ashtakavarga.bhinna || {})[planet]?.by_sign || [])
                    .find(item => item.sign_index === savRow.sign_index);
                row.push(bavRow ? bavRow.bindus : '');
            });
            return row;
        });
}

function expertYogaRows(data) {
    return ((data.yogas && data.yogas.matches) || []).map(match => [
        match.name,
        match.topic,
        match.effect_type,
        match.strength,
        match.confidence,
        match.rule,
    ]);
}

function expertGenericActiveDashaRows(dashaLayer) {
    if (!dashaLayer || !Object.keys(dashaLayer).length) {
        return [['status', 'not_available', '', '', 'API response içinde aktif periyot yok']];
    }

    const active = dashaLayer.current_active || dashaLayer.active || {};
    const rows = ['maha', 'antara', 'pratyantar', 'sookshma']
        .filter(level => active[level])
        .map(level => {
            const period = active[level];
            return [
                level,
                period.yogini || period.lord || period.rashi || period.sign || '',
                period.start || '',
                period.end || '',
                period.effective_years || period.years || '',
            ];
        });

    if (!rows.length && Object.keys(active).length) {
        rows.push([
            'active',
            active.yogini || active.lord || active.rashi || active.sign || active.path || '',
            active.start || '',
            active.end || '',
            active.effective_years || active.years || '',
        ]);
    }

    return rows.length ? rows : [['status', 'not_available', '', '', 'API response içinde aktif periyot yok']];
}

function expertGrahaYuddhaRows(data) {
    return (data.planets || []).map(planet => {
        const war = planet.war || {};
        return [
            planet.name,
            war.status,
            war.in_graha_yuddha ? 'evet' : 'hayır',
            war.opponent,
            war.orb,
            'winner/loser hesaplanmıyor; orb bazlı teknik durum',
        ];
    });
}

function expertVargaStatusRows(data, divisions) {
    const vargas = data.vargas || {};
    return divisions.map(division => [
        division,
        vargas[division] ? 'available' : 'not_available',
        vargas[division] ? (vargas[division].name || '') : '',
    ]);
}

function expertPanchangaReferenceRows(data) {
    const panchanga = data.panchanga || {};
    const reference = panchanga.reference || {};
    return [
        ['Input source', panchanga.input_source || ''],
        ['Method', panchanga.method || ''],
        ['Yerel tarih', reference.date || ''],
        ['Yerel saat', reference.time || ''],
        ['Yerel datetime', reference.local_datetime || ''],
        ['UTC datetime', reference.utc_datetime || ''],
        ['Timezone', reference.timezone_id || ''],
        ['UTC farkı', reference.tz_offset ?? ''],
        ['Julian day', reference.julian_day ?? ''],
        ['Konum', reference.place || ''],
        ['Koordinat', `${reference.latitude ?? ''}, ${reference.longitude_geo ?? ''}`],
    ];
}

function expertPanchangaCoreRows(data) {
    const panchanga = data.panchanga || {};
    const tithi = panchanga.tithi || {};
    const paksha = panchanga.paksha || {};
    const vara = panchanga.vara || {};
    const yoga = panchanga.yoga || {};
    const karana = panchanga.karana || {};
    const moonNakshatra = panchanga.moon_nakshatra || {};
    return [
        ['Tithi', tithi.name || '', tithi.number ?? '', tithi.paksha_tithi ?? '', tithi.elapsed_degrees ?? '', tithi.remaining_degrees ?? ''],
        ['Paksha', paksha.name || '', paksha.phase || '', '', '', ''],
        ['Vara', vara.name || '', vara.sanskrit || '', vara.weekday_index ?? '', '', ''],
        ['Yoga', yoga.name || '', yoga.number ?? '', '', yoga.elapsed_degrees ?? '', yoga.remaining_degrees ?? ''],
        ['Karana', karana.name || '', karana.number ?? '', '', karana.elapsed_degrees ?? '', karana.remaining_degrees ?? ''],
        ['Ay Nakshatra', moonNakshatra.name || '', moonNakshatra.number ?? '', moonNakshatra.pada ?? '', moonNakshatra.lord || '', moonNakshatra.degree_str || ''],
    ];
}

function expertPanchangaCartographyRows(data) {
    const seed = data.panchanga && data.panchanga.cartography_seed ? data.panchanga.cartography_seed : {};
    return [
        ['Status', seed.status || ''],
        ['Coordinate system', seed.coordinate_system || ''],
        ['Time basis', seed.time_basis || ''],
        ['Required', (seed.requires_for_astrocartography || []).join(', ')],
        ['Available', (seed.available_layers || []).join(', ')],
        ['Missing', (seed.missing_layers || []).join(', ')],
    ];
}

function expertPanchangaPlanetRows(data) {
    return ((data.panchanga && data.panchanga.planetary_positions) || []).map(row => [
        row.planet,
        row.sign_tr,
        row.sign,
        row.degree_str,
        row.longitude,
    ]);
}

function expertLifeDashaRows(lifePeriod, level) {
    return (((lifePeriod.vimshottari_dasha_timeline || {})[level]) || []).map(row => [
        row.lord,
        row.parent_lord || '',
        row.start_date,
        row.end_date,
        row.age_start,
        row.age_end,
    ]);
}

function expertLifeTransitRows(lifePeriod, key) {
    return (((lifePeriod[key] || {}).periods) || []).map(row => [
        row.start_date,
        row.end_date,
        row.age_start,
        row.age_end,
        row.sign,
        row.house_from_lagna,
        row.house_from_moon,
        (row.vedic_aspects || []).map(item => item.house_from_lagna).join(', '),
        (row.vedic_aspects || []).map(item => item.house_from_moon).join(', '),
        (row.natal_planet_contacts || []).map(contact => `${contact.natal_planet}:${contact.contact_type}`).join('; '),
    ]);
}

function expertLifeRetrogradeRows(lifePeriod, key) {
    return (((lifePeriod[key] || {}).retrograde_periods) || []).map(row => [
        row.planet,
        row.start_date,
        row.end_date,
    ]);
}

function expertLifeCombinedRows(lifePeriod) {
    return (lifePeriod.saturn_jupiter_combined_periods || []).map(row => [
        row.start_date,
        row.end_date,
        row.age_start,
        row.age_end,
        row.saturn ? row.saturn.sign : '',
        row.saturn ? row.saturn.house_from_lagna : '',
        row.saturn ? row.saturn.house_from_moon : '',
        row.jupiter ? row.jupiter.sign : '',
        row.jupiter ? row.jupiter.house_from_lagna : '',
        row.jupiter ? row.jupiter.house_from_moon : '',
    ]);
}

function expertLifeOverlapRows(lifePeriod) {
    return (lifePeriod.dasha_transit_overlap_periods || []).map(row => [
        row.start_date,
        row.end_date,
        row.age_start,
        row.age_end,
        row.dasha_level,
        row.dasha_lord,
        row.transit_planet,
        row.transit_sign,
        row.overlap_flags ? row.overlap_flags.same_dasha_and_transit_planet : '',
        row.overlap_flags ? row.overlap_flags.transit_contacts_dasha_lord : '',
    ]);
}

function expertLifePeriodMarkdown(data) {
    const lifePeriod = data.life_period_analysis || {};
    if (!Object.keys(lifePeriod).length) {
        return [
            '## Uzun Dönem Dasha + Satürn/Jüpiter Transit Teknik Tablosu',
            '',
            '- Durum: not_available',
            '- Not: Bu paket chart verisine life_period_analysis eklenmeden üretildi.',
        ].join('\n');
    }
    if (lifePeriod.status === 'not_available' || !lifePeriod.analysis_period) {
        return [
            '## Uzun Dönem Dasha + Satürn/Jüpiter Transit Teknik Tablosu',
            '',
            '- Durum: not_available',
            `- Sebep: ${lifePeriod.error || 'life_period_analysis teknik tablosu yok'}`,
        ].join('\n');
    }

    const analysis = lifePeriod.analysis_period || {};
    const saturn = lifePeriod.saturn_transit_timeline || {};
    const jupiter = lifePeriod.jupiter_transit_timeline || {};
    return [
        '## Uzun Dönem Dasha + Satürn/Jüpiter Transit Teknik Tablosu',
        '',
        `- Başlangıç yaşı: ${analysis.from_age || ''}`,
        `- Tarih aralığı: ${analysis.start_date || ''} → ${analysis.to_date || ''}`,
        '- Dasha seviyesi: Maha + Antardasha',
        '- Yorum: yok; teknik tablo.',
        '',
        '### Life Maha Dasha',
        '',
        markdownTable(['Lord', 'Parent', 'Başlangıç', 'Bitiş', 'Yaş Baş.', 'Yaş Bit.'], expertLifeDashaRows(lifePeriod, 'maha')),
        '',
        '### Life Antardasha',
        '',
        markdownTable(['Lord', 'Parent', 'Başlangıç', 'Bitiş', 'Yaş Baş.', 'Yaş Bit.'], expertLifeDashaRows(lifePeriod, 'antara')),
        '',
        '### Saturn Sidereal Transit Periods',
        '',
        `- Method: ${saturn.method || ''}`,
        '',
        markdownTable(['Başlangıç', 'Bitiş', 'Yaş Baş.', 'Yaş Bit.', 'Burç', 'Lagna Ev', 'Ay Ev', 'Drishti Lagna Evleri', 'Drishti Ay Evleri', 'Natal Temas'], expertLifeTransitRows(lifePeriod, 'saturn_transit_timeline')),
        '',
        '### Saturn Retrograde Periods',
        '',
        markdownTable(['Gezegen', 'Başlangıç', 'Bitiş'], expertLifeRetrogradeRows(lifePeriod, 'saturn_transit_timeline')),
        '',
        '### Jupiter Sidereal Transit Periods',
        '',
        `- Method: ${jupiter.method || ''}`,
        '',
        markdownTable(['Başlangıç', 'Bitiş', 'Yaş Baş.', 'Yaş Bit.', 'Burç', 'Lagna Ev', 'Ay Ev', 'Drishti Lagna Evleri', 'Drishti Ay Evleri', 'Natal Temas'], expertLifeTransitRows(lifePeriod, 'jupiter_transit_timeline')),
        '',
        '### Jupiter Retrograde Periods',
        '',
        markdownTable(['Gezegen', 'Başlangıç', 'Bitiş'], expertLifeRetrogradeRows(lifePeriod, 'jupiter_transit_timeline')),
        '',
        '### Saturn + Jupiter Combined Periods',
        '',
        markdownTable(['Başlangıç', 'Bitiş', 'Yaş Baş.', 'Yaş Bit.', 'Saturn Burç', 'Saturn Lagna Ev', 'Saturn Ay Ev', 'Jupiter Burç', 'Jupiter Lagna Ev', 'Jupiter Ay Ev'], expertLifeCombinedRows(lifePeriod)),
        '',
        '### Dasha Transit Overlap Periods',
        '',
        markdownTable(['Başlangıç', 'Bitiş', 'Yaş Baş.', 'Yaş Bit.', 'Dasha Seviye', 'Dasha Lord', 'Transit', 'Transit Burç', 'Aynı Gezegen', 'Dasha Lord Temas'], expertLifeOverlapRows(lifePeriod)),
    ].join('\n');
}

function selectedAnalysisModeProfile() {
    const select = document.getElementById('analysis-mode');
    const mode = select && ANALYSIS_MODE_PROFILES[select.value] ? select.value : 'client';
    return ANALYSIS_MODE_PROFILES[mode];
}

function applyAnalysisModeToChart(chart) {
    if (!chart) return chart;
    chart.analysis_profile = selectedAnalysisModeProfile();
    return chart;
}

function vaultSaveChartPayload(chart) {
    const payload = { ...chart };
    delete payload.life_period_analysis;
    return payload;
}

function analysisModeMarkdownRows(profile) {
    return [
        ['analysis_mode', profile.mode],
        ['label', profile.label],
        ['interpretation_language', profile.interpretation_language],
        ['certainty_policy', profile.certainty_policy],
        ['usage_rule', profile.usage_rule],
    ];
}

function backendExpertCopyPackage(data) {
    return data && data.copy_packages && data.copy_packages.expert
        ? data.copy_packages.expert
        : null;
}

function backendExpertCopyMarkdown(data) {
    const pkg = backendExpertCopyPackage(data);
    if (!pkg || typeof pkg.markdown !== 'string' || !pkg.markdown.trim()) {
        return '';
    }
    const currentProfile = data.analysis_profile || selectedAnalysisModeProfile();
    const packageProfile = pkg.analysis_profile || {};
    if (currentProfile.mode && packageProfile.mode && currentProfile.mode !== packageProfile.mode) {
        return '';
    }
    return pkg.markdown;
}

async function readJsonResponse(response, fallbackMessage) {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
        return response.json();
    }
    const text = await response.text();
    const statusText = `${response.status} ${response.statusText || ''}`.trim();
    const htmlReturned = text.trim().startsWith('<');
    const detail = response.status === 404
        ? 'Endpoint bulunamadı; backend sunucusunu yeniden başlatmak gerekebilir.'
        : htmlReturned
            ? 'Backend JSON yerine HTML hata sayfası döndürdü.'
            : text.trim().slice(0, 160);
    throw new Error(`${fallbackMessage}: ${statusText}. ${detail}`);
}

async function fetchBackendExpertCopyPackage(data) {
    const chartPayload = { ...data };
    delete chartPayload.copy_packages;
    const response = await fetch('/api/v2/chart/expert-copy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            chart: chartPayload,
            person: lastPersonInfo || (data.birth && data.birth.person) || {},
            analysis_profile: selectedAnalysisModeProfile(),
        }),
    });
    const result = await readJsonResponse(response, 'Uzman kopya paketi alınamadı');
    if (!response.ok) {
        throw new Error(result.error || 'Uzman kopya paketi üretilemedi');
    }
    const pkg = result.copy_packages && result.copy_packages.expert;
    if (!pkg || typeof pkg.markdown !== 'string') {
        throw new Error('Uzman kopya paketi cevabı eksik');
    }
    data.copy_packages = {
        ...(data.copy_packages || {}),
        expert: pkg,
    };
    data.analysis_profile = pkg.analysis_profile || data.analysis_profile;
    return pkg.markdown;
}

function generateExpertCopyPackage(data) {
    const backendMarkdown = backendExpertCopyMarkdown(data);
    if (backendMarkdown) {
        return backendMarkdown;
    }

    const analysisProfile = data.analysis_profile || selectedAnalysisModeProfile();
    const person = lastPersonInfo || {};
    const birth = data.birth || data.birth_info || {};
    const meta = data.meta || {};
    const ayanamsa = meta.ayanamsa || data.ayanamsa || {};
    const lagna = data.lagna || {};
    const moon = (data.planets || []).find(planet => planet.name === 'Moon') || {};
    const sun = (data.planets || []).find(planet => planet.name === 'Sun') || {};
    const jaimini = data.jaimini || {};
    const karakamsa = jaimini.karakamsa || {};
    const arudha = jaimini.arudha || {};
    const upapada = arudha.upapada_detail || {};
    const doshas = data.doshas || {};
    const shadbala = data.shadbala || {};
    const kp = data.kp || {};
    const ashtakavarga = data.ashtakavarga || {};
    const varshaphala = data.varshaphala || {};
    const sav = ashtakavarga.sarva || ashtakavarga.sarvashtakavarga || {};
    const bavHeaders = expertBavHeaders(data);
    const vargaMarkdownSections = VARGA_DIVISIONS.flatMap(division => {
        const title = VARGA_TITLES[division] || division;
        return [
            `## ${title} Full Tablo`,
            '',
            markdownTable(['Nokta', `${division} Burç`, `${division} Derece`], expertVargaRows(data, division)),
            '',
        ];
    });
    const dashas = data.dashas || {};

    const planetRows = (data.planets || []).map(planet => [
        planet.name,
        markdownSign(planet),
        planet.house,
        planet.degree_str,
        planet.nakshatra ? planet.nakshatra.name : '',
        planet.nakshatra ? planet.nakshatra.pada : '',
        planet.nakshatra ? planet.nakshatra.lord : '',
        planet.dignity ? planet.dignity.essential : '',
        planet.combustion ? planet.combustion.severity : '',
        planet.war ? planet.war.status : '',
        planet.motion && planet.motion.retrograde ? 'R' : '',
    ]);
    const shadbalaRows = (shadbala.planets || []).map(row => [
        row.planet,
        row.total_score,
        row.grade,
        row.components && row.components.sthana_bala ? row.components.sthana_bala.score : '',
        row.components && row.components.kala_bala ? row.components.kala_bala.score : '',
        row.components && row.components.drik_bala ? row.components.drik_bala.score : '',
        row.components && row.components.yuddha_bala ? row.components.yuddha_bala.score_adjustment : '',
    ]);
    const kpRows = (kp.planets || []).map(planet => [
        planet.planet,
        markdownSign(planet),
        planet.nakshatra_lord,
        planet.sub_lord,
        planet.sub_sub_lord,
    ]);
    const kpHouseRows = kp.significators && kp.significators.house_significators
        ? Object.entries(kp.significators.house_significators).map(([house, rows]) => [
            house,
            (rows || []).slice(0, 7).map(row => `${row.planet}(${row.score})`).join(', '),
        ])
        : [];
    const karakamsaRows = Array.isArray(karakamsa.d9_planets_from_karakamsa)
        ? karakamsa.d9_planets_from_karakamsa.map(row => [
            row.planet,
            markdownSign(row),
            row.degree_str,
            row.house_from_karakamsa,
            row.house_class,
        ])
        : [];
    const varshaPlanetRows = Array.isArray(varshaphala.planets)
        ? varshaphala.planets.map(row => [
            row.name,
            markdownSign(row),
            row.degree_str,
            row.house,
            row.natal_house,
        ])
        : [];
    const yearLord = varshaphala.year_lord && varshaphala.year_lord.selected
        ? varshaphala.year_lord.selected
        : {};
    const muddaActive = varshaphala.mudda_dasha && varshaphala.mudda_dasha.active
        ? varshaphala.mudda_dasha.active
        : {};
    return [
        `# ${person.name || birth.person?.name || 'Danışan'} Teknik Harita Paketi`,
        '',
        '## Kimlik ve Hesap Ayarları',
        '',
        `- İsim: ${person.name || birth.person?.name || ''}`,
        `- Grup: ${person.group || ''}`,
        `- Doğum: ${birth.date || ''} ${birth.time || ''}`,
        `- Yer: ${birth.place || ''}`,
        `- Saat dilimi: ${birth.timezone_label || birth.timezone || ''}`,
        `- Koordinatlar: ${birth.latitude || ''}, ${birth.longitude_geo || ''}`,
        `- Saat güveni: ${birth.time_confidence_label || formatQualityValue(birth.time_confidence)}`,
        `- Ayanamsa: ${ayanamsa.type || ''} ${ayanamsa.value || ''}`,
        `- House system: ${meta.house_system || ''}`,
        '',
        '## Yorum Dili / Analiz Modu',
        '',
        markdownTable(['Alan', 'Değer'], analysisModeMarkdownRows(analysisProfile)),
        '',
        '## Ana Göstergeler',
        '',
        `- Lagna: ${markdownSign(lagna)} ${lagna.degree_str || ''}`,
        `- Moon: ${markdownSign(moon)} ${moon.degree_str || ''}`,
        `- Sun: ${markdownSign(sun)} ${sun.degree_str || ''}`,
        `- Atmakaraka: ${karakamsa.atmakaraka || ''}`,
        `- Karakamsa: ${markdownSign(karakamsa.karakamsa_lagna)}`,
        `- Upapada: ${markdownSign(arudha.upapada && arudha.upapada.pada)}`,
        '',
        '## Panchanga Teknik Paketi',
        '',
        '- Bu bölüm Panchanga referans anı ve konumu için teknik veri paketidir; yorum veya muhurta hükmü değildir.',
        '',
        '### Panchanga Referansı',
        '',
        markdownTable(['Alan', 'Değer'], expertPanchangaReferenceRows(data)),
        '',
        '### Panchanga Angaları',
        '',
        markdownTable(['Anga', 'Ad', 'No/Faz', 'Pada/Index', 'Ek', 'Kalan/Der.'], expertPanchangaCoreRows(data)),
        '',
        '### Kartografi Çekirdeği',
        '',
        markdownTable(['Alan', 'Değer'], expertPanchangaCartographyRows(data)),
        '',
        '### Panchanga Gezegen Boylamları',
        '',
        markdownTable(['Gezegen', 'Burç TR', 'Burç', 'Derece', 'Boylam'], expertPanchangaPlanetRows(data)),
        '',
        '## Aktif Vimshottari',
        '',
        markdownTable(['Seviye', 'Lord', 'Başlangıç', 'Bitiş', 'Yıl'], activeDashaRows(data)),
        '',
        '## D1 Gezegen Tablosu',
        '',
        markdownTable(['Gezegen', 'Burç', 'Ev', 'Derece', 'Nakshatra', 'Pada', 'Lord', 'Dignity', 'Combustion', 'War', 'R'], planetRows),
        '',
        ...vargaMarkdownSections,
        '## Shadbala',
        '',
        markdownTable(['Gezegen', 'Toplam', 'Seviye', 'Sthana', 'Kala', 'Drik', 'Yuddha Adj.'], shadbalaRows),
        '',
        '## KP Star / Sub / Sub-Sub',
        '',
        markdownTable(['Gezegen', 'Burç', 'Star Lord', 'Sub Lord', 'Sub-Sub Lord'], kpRows),
        '',
        '## KP House Significators',
        '',
        markdownTable(['Ev', 'Significator Gezegenler'], kpHouseRows),
        '',
        '## Jaimini',
        '',
        `- Arudha Lagna: ${markdownSign(arudha.padas && arudha.padas.A1 && arudha.padas.A1.pada)}`,
        `- Upapada Lord: ${upapada.upapada_lord ? upapada.upapada_lord.planet : ''}`,
        `- 2nd From UL: ${markdownSign(upapada.second_from_upapada)}`,
        '',
        markdownTable(['D9 Gezegen', 'D9 Burç', 'Derece', 'Karakamsa’dan Ev', 'Sınıf'], karakamsaRows),
        '',
        '## Chara Dasha Aktif Periyotlar',
        '',
        markdownTable(['Seviye', 'Lord/Rashi', 'Başlangıç', 'Bitiş', 'Yıl/Not'], expertGenericActiveDashaRows(dashas.chara)),
        '',
        '## Yogini Dasha Aktif Periyotlar',
        '',
        markdownTable(['Seviye', 'Lord/Rashi', 'Başlangıç', 'Bitiş', 'Yıl/Not'], expertGenericActiveDashaRows(dashas.yogini)),
        '',
        '## Yoga Listesi',
        '',
        markdownTable(['Yoga', 'Konu', 'Etki', 'Güç', 'Güven', 'Kural'], expertYogaRows(data)),
        '',
        '## Dosha Teknik Özeti',
        '',
        `- Mangala: ${doshas.mangala ? doshas.mangala.status : ''} / ${doshas.mangala ? doshas.mangala.net_severity || doshas.mangala.severity : ''}`,
        `- Kala Sarpa: ${doshas.kala_sarpa ? doshas.kala_sarpa.status : ''} / ${doshas.kala_sarpa ? doshas.kala_sarpa.subtype || '' : ''}`,
        '',
        '## Ashtakavarga',
        '',
        `- SAV toplam: ${sav.total || ''}`,
        `- Ruleset: ${ashtakavarga.ruleset ? ashtakavarga.ruleset.name || ashtakavarga.ruleset.method || '' : ''}`,
        '',
        '### SAV per House',
        '',
        markdownTable(['Ev', 'Burç', 'SAV'], expertSavRows(data)),
        '',
        '### BAV per House',
        '',
        markdownTable(['Ev', 'Burç', ...bavHeaders], expertBavRows(data)),
        '',
        '## Bhava Chalit',
        '',
        '- Durum: API response içinde bhava_chalit alanı yok; Whole Sign ev sistemi korunuyor.',
        '',
        '## Graha Yuddha Sonucu',
        '',
        markdownTable(['Gezegen', 'Durum', 'Savaşta', 'Rakip', 'Orb', 'Sonuç'], expertGrahaYuddhaRows(data)),
        '',
        expertLifePeriodMarkdown(data),
        '',
        '## Varshaphala',
        '',
        `- Varsha başlangıcı: ${varshaphala.year ? varshaphala.year.start_local || '' : ''}`,
        `- Varsha Lagna: ${markdownSign(varshaphala.varsha_lagna)}`,
        `- Muntha: ${markdownSign(varshaphala.muntha)} / Ev ${varshaphala.muntha ? varshaphala.muntha.house_from_varsha_lagna || '' : ''}`,
        `- Yıl Lordu: ${yearLord.planet || ''}`,
        `- Aktif Mudda: ${muddaActive.lord || ''}`,
        '',
        markdownTable(['Gezegen', 'Varsha Burç', 'Derece', 'Yıllık Ev', 'Natal Ev'], varshaPlanetRows),
        '',
        '## Teknik Not',
        '',
        '- Bu paket API hesap parametreleridir; yorum veya kehanet metni değildir.',
        '- Varyantlı alanlarda API içindeki method/source_rule/assumptions/excluded_rules alanları esas alınmalıdır.',
    ].join('\n');
}

async function renderExpertCopyPackage(data) {
    const container = document.getElementById('expert-copy-content');
    if (!container) return false;
    const chart = applyAnalysisModeToChart(data);
    const requestId = ++expertCopyRenderRequestId;
    const cachedMarkdown = backendExpertCopyMarkdown(chart);
    if (cachedMarkdown) {
        container.textContent = cachedMarkdown;
        return true;
    }

    container.textContent = '';
    try {
        const markdown = await fetchBackendExpertCopyPackage(chart);
        if (requestId === expertCopyRenderRequestId && markdown) {
            container.textContent = markdown;
        }
        return Boolean(markdown);
    } catch (err) {
        if (requestId === expertCopyRenderRequestId) {
            setVaultStatus(err.message, 'error');
        }
        return false;
    }
}

async function copyExpertPackage() {
    if (lastChartData) {
        const rendered = await renderExpertCopyPackage(lastChartData);
        if (!rendered) return;
    }
    const container = document.getElementById('expert-copy-content');
    if (!container || !container.textContent.trim()) {
        setVaultStatus('Önce harita hesapla.', 'error');
        return;
    }
    try {
        await navigator.clipboard.writeText(container.textContent);
        setVaultStatus('Uzman kopya paketi panoya alındı.', 'success');
    } catch (err) {
        setVaultStatus('Kopyalama tarayıcı tarafından engellendi; metni elle seçebilirsin.', 'error');
    }
}

function extractYear(dateText) {
    const match = String(dateText || '').match(/\b(\d{4})\b/);
    return match ? Number(match[1]) : null;
}

function dashaChildren(period) {
    const childKey = DASHA_CHILD_KEY[period.level || 'maha'];
    return childKey ? (period[childKey] || []) : [];
}

function dashaRowHtml(period, id, parentId, depth, visible) {
    const children = dashaChildren(period);
    const hasChildren = children.length > 0;
    const badge = period.is_birth_dasha || period.active_at_birth
        ? '<span class="birth-badge">doğum</span>'
        : '';
    const yearCount = typeof period.effective_years === 'number'
        ? period.effective_years.toFixed(period.effective_years < 1 ? 4 : 2)
        : '';
    const toggle = hasChildren ? '<span class="dasha-toggle">▸</span>' : '<span class="dasha-toggle empty"></span>';

    return `<tr class="dasha-row depth-${depth}" data-dasha-id="${id}" data-parent-id="${parentId || ''}" data-depth="${depth}" style="${visible ? '' : 'display:none'}">
        <td>${DASHA_LEVEL_LABEL[period.level] || period.level || 'Maha'}</td>
        <td class="dasha-lord" style="padding-left:${0.75 + depth * 1.2}rem">${toggle}<span style="font-weight:600">${period.lord}</span></td>
        <td>${yearCount}</td>
        <td>${period.start}</td>
        <td>${period.end}</td>
        <td>${badge}</td>
    </tr>`;
}

function removeDashaDescendants(tbody, parentId) {
    const children = Array.from(tbody.querySelectorAll(`tr[data-parent-id="${parentId}"]`));
    for (const child of children) {
        removeDashaDescendants(tbody, child.dataset.dashaId);
        child.remove();
    }
}

function toggleDashaRow(row, periodById, tbody) {
    const id = row.dataset.dashaId;
    const period = periodById.get(id);
    const children = dashaChildren(period);
    if (children.length === 0) return;

    const toggle = row.querySelector('.dasha-toggle');
    const existingChildren = tbody.querySelector(`tr[data-parent-id="${id}"]`);
    if (existingChildren) {
        removeDashaDescendants(tbody, id);
        toggle.textContent = '▸';
        return;
    }

    const depth = Number(row.dataset.depth || 0) + 1;
    const rows = [];
    children.forEach((child, index) => {
        const childId = `${id}.${index}`;
        periodById.set(childId, child);
        rows.push(dashaRowHtml(child, childId, id, depth, true));
    });
    row.insertAdjacentHTML('afterend', rows.join(''));
    toggle.textContent = '▾';
}

function renderDashaTable(data) {
    const tbody = document.querySelector('#dasha-table tbody');
    const dashas = data.dashas ? data.dashas.vimshottari.maha : data.vimshottari_dasha;
    const visibleDashas = dashas.filter(d => {
        const startYear = extractYear(d.start);
        return startYear === null || startYear <= DASHAS_UNTIL_YEAR;
    });
    const periodById = new Map();
    const rows = visibleDashas.map((period, index) => {
        const id = String(index);
        periodById.set(id, period);
        return dashaRowHtml(period, id, '', 0, true);
    });

    tbody.innerHTML = rows.join('') || '<tr><td colspan="6">2050’ye kadar gösterilecek Maha Dasha yok</td></tr>';
    tbody.onclick = function(event) {
        const row = event.target.closest('.dasha-row');
        if (!row || !tbody.contains(row)) return;
        toggleDashaRow(row, periodById, tbody);
    };
}

const RECTIFICATION_EVENT_TYPES = [
    'career',
    'family',
    'marriage',
    'divorce',
    'childbirth',
    'education',
    'relocation',
    'health',
    'accident',
    'surgery',
    'death_family',
    'wealth',
    'property',
    'business',
    'legal',
    'spiritual_shift'
];

function rectificationEventTypeOptions(selectedType) {
    return RECTIFICATION_EVENT_TYPES.map(type => {
        const selected = type === selectedType ? ' selected' : '';
        return `<option value="${escapeHTML(type)}"${selected}>${escapeHTML(type)}</option>`;
    }).join('');
}

function createRectificationEventRow(selectedType = 'career', eventData = {}) {
    const container = document.getElementById('rectification-events');
    if (!container) return;
    const type = eventData.type || selectedType;
    const date = eventData.date || '';
    const time = eventData.time || '12:00';
    const confidence = eventData.confidence || 'medium';
    const certainty = eventData.certainty || 'day_exact';

    const row = document.createElement('div');
    row.className = 'rectification-event-row';
    row.innerHTML = `
        <select class="rect-event-type">${rectificationEventTypeOptions(type)}</select>
        <input type="date" class="rect-event-date" value="${escapeHTML(date)}">
        <input type="time" class="rect-event-time" value="${escapeHTML(time)}">
        <select class="rect-event-certainty">
            <option value="day_exact"${certainty === 'day_exact' ? ' selected' : ''}>gün net</option>
            <option value="month_known"${certainty === 'month_known' ? ' selected' : ''}>ay net</option>
            <option value="year_known"${certainty === 'year_known' ? ' selected' : ''}>yıl net</option>
            <option value="approximate"${certainty === 'approximate' ? ' selected' : ''}>yaklaşık</option>
        </select>
        <select class="rect-event-confidence">
            <option value="high"${confidence === 'high' ? ' selected' : ''}>yüksek</option>
            <option value="medium"${confidence === 'medium' ? ' selected' : ''}>orta</option>
            <option value="low"${confidence === 'low' ? ' selected' : ''}>düşük</option>
        </select>
        <button class="btn-copy rect-event-remove" type="button" aria-label="Olayı sil">Sil</button>
    `;
    container.appendChild(row);
}

function seedRectificationEventRows(seedEvents = null) {
    const container = document.getElementById('rectification-events');
    if (!container || container.children.length) return;
    const events = seedEvents && seedEvents.length ? seedEvents : [
        'career',
        'marriage',
        'childbirth',
        'relocation',
        'health',
        'education',
        'wealth',
        'property',
        'accident',
        'spiritual_shift'
    ].map(type => ({ type }));
    events.forEach(event => createRectificationEventRow(event.type || 'career', event));
}

function loadRectificationEventsForCurrentPerson() {
    const container = document.getElementById('rectification-events');
    if (!container) return;
    container.innerHTML = '';
    seedRectificationEventRows(loadSavedRectificationEvents());
}

function setRectificationEventRows(events, persist = false) {
    const container = document.getElementById('rectification-events');
    if (!container) return;
    container.innerHTML = '';
    seedRectificationEventRows(events);
    if (persist) {
        saveRectificationEventsForCurrentPerson();
    }
}

function collectRectificationEvents() {
    return Array.from(document.querySelectorAll('.rectification-event-row'))
        .map(row => {
            const date = row.querySelector('.rect-event-date').value;
            if (!date) return null;
            return {
                type: row.querySelector('.rect-event-type').value,
                date,
                time: row.querySelector('.rect-event-time').value || '12:00',
                certainty: row.querySelector('.rect-event-certainty').value,
                confidence: row.querySelector('.rect-event-confidence').value
            };
        })
        .filter(Boolean);
}

function saveRectificationEventsForCurrentPerson() {
    const key = rectificationPersonKey();
    if (!key) return;
    const events = collectRectificationEvents();
    const store = loadRectificationEventStore();
    if (events.length) {
        store[key] = events;
    } else {
        delete store[key];
    }
    persistRectificationEventStore(store);
}

function rectificationStepLabel(searchWindow) {
    if (!searchWindow) return '-';
    const minutes = Number(searchWindow.step_minutes || 0);
    const seconds = Number(searchWindow.step_seconds || 0);
    const parts = [];
    if (minutes) parts.push(`${minutes} dk`);
    if (seconds) parts.push(`${seconds} sn`);
    return parts.length ? parts.join(' ') : '-';
}

function normalizeRectificationTimeLabel(value) {
    const parts = String(value || '').split(':').map(part => Number(part));
    if (parts.length < 2 || parts.some(part => Number.isNaN(part))) return '';
    const [hour, minute, second = 0] = parts;
    return [hour, minute, second].map(part => String(part).padStart(2, '0')).join(':');
}

function currentRectificationProductStatus() {
    if (lastRectificationDecision && lastRectificationDecision.product_status) {
        return lastRectificationDecision.product_status;
    }
    if (activeRectificationRecord && activeRectificationRecord.rectification_v1_status) {
        return activeRectificationRecord.rectification_v1_status;
    }
    return {};
}

function chartBirthTimeLabelForSave(chart) {
    const birth = chart && chart.birth ? chart.birth : {};
    const chartTime = normalizeRectificationTimeLabel(birth.time);
    if (chartTime) return chartTime;
    return normalizeRectificationTimeLabel([
        document.getElementById('hour').value || '00',
        document.getElementById('minute').value || '00',
        document.getElementById('second').value || '00'
    ].join(':'));
}

function vaultRectifiedTimeSaveBlockReason(chart) {
    const birth = chart && chart.birth ? chart.birth : {};
    const formClaimsRectified = birthTimeConfidenceForForm() === 'rectified';
    const chartClaimsRectified = birth.rectification_status === 'yapıldı' || birth.time_confidence === 'rectified';
    if (!formClaimsRectified && !chartClaimsRectified) {
        return '';
    }
    if (birth.rectification_source === 'external_astrolog_or_user_confirmed') {
        return '';
    }

    const productStatus = currentRectificationProductStatus();
    const requestedTime = chartBirthTimeLabelForSave(chart);
    const suggestedTime = normalizeRectificationTimeLabel(productStatus.suggested_time);
    if (productStatus.can_save_rectified_time !== true) {
        const code = productStatus.code || 'v1_gate_missing';
        return `Rektifiye saat için v1 karar kapısı açık değil (${code}). Önce rektifikasyon analizini çalıştır.`;
    }
    if (suggestedTime && requestedTime && suggestedTime !== requestedTime) {
        return `v1 karar kapısı ${suggestedTime} saatini öneriyor; ${requestedTime} için yeniden analiz gerekli.`;
    }
    return '';
}

function rectificationDecisionSaveBlockReason(decision, requestedTime) {
    if (!decision) {
        return 'Önce rektifikasyon analizini çalıştır. Karar kapısı olmadan rektifiye saat kaydedilmez.';
    }
    const productStatus = decision.product_status || {};
    const productAllowsSave = productStatus.can_save_rectified_time;
    const legacyAllowsSave = decision.status === 'candidate_for_review' && decision.selection_allowed;
    const canSave = typeof productAllowsSave === 'boolean'
        ? productAllowsSave
        : legacyAllowsSave;
    if (!canSave) {
        const reason = decision.reason || 'Karar kapısı bu sonucu final saat kaydına uygun görmedi.';
        const code = productStatus.code || decision.status || 'unknown';
        return `Rektifikasyon henüz kayda hazır değil (${code}): ${reason}`;
    }
    const suggestedTime = normalizeRectificationTimeLabel(
        productStatus.suggested_time || decision.suggested_time
    );
    const normalizedRequestedTime = normalizeRectificationTimeLabel(requestedTime);
    if (suggestedTime && normalizedRequestedTime && suggestedTime !== normalizedRequestedTime) {
        return `Karar kapısı ${suggestedTime} saatini öneriyor; farklı saat kaydetmeden önce analizi tekrar çalıştır.`;
    }
    return '';
}

function rectificationDecisionLabel(status) {
    return {
        not_ready: 'Hazır değil',
        ambiguous: 'Belirsiz',
        review_window: 'Pencere incele',
        candidate_for_review: 'Aday incele'
    }[status] || formatQualityValue(status || 'unknown');
}

function renderRectificationDecision(decision) {
    if (!decision) {
        return '<p class="layer-empty">Karar özeti yok.</p>';
    }
    const productStatus = decision.product_status || {};
    const decisionLabel = productStatus.label_tr || rectificationDecisionLabel(decision.status);
    const decisionCode = productStatus.code || decision.status || 'unknown';
    const showSuggestion = decision.status === 'candidate_for_review' && decision.selection_allowed;
    const suggestedWindow = showSuggestion && decision.suggested_window
        ? `${decision.suggested_window.start_time || '-'} - ${decision.suggested_window.end_time || '-'}`
        : '-';
    const suggested = showSuggestion ? (decision.suggested_time || suggestedWindow) : '-';
    return `
        <div class="rectification-decision rectification-decision-${escapeHTML(decision.status || 'unknown')}">
            <div class="rectification-decision-main">
                <span>Karar Kapısı</span>
                <strong>${escapeHTML(decisionLabel)}</strong>
            </div>
            <div>
                <span>v1 Kod</span>
                <strong>${escapeHTML(decisionCode)}</strong>
            </div>
            <div>
                <span>Seçilebilir Saat</span>
                <strong>${escapeHTML(suggested || '-')}</strong>
            </div>
            <div>
                <span>Skor Farkı</span>
                <strong>${escapeHTML(decision.score_gap ?? '-')}</strong>
            </div>
            <div>
                <span>Gerekçe</span>
                <strong>${escapeHTML(decision.reason || '-')}</strong>
            </div>
        </div>
    `;
}

function buildRectificationPayload() {
    const events = collectRectificationEvents();
    if (events.length < 5) {
        throw new Error('Profesyonel rektifikasyon için en az 5 olay gir. İdeal aralık 8-20 olay.');
    }
    const hour = Number(document.getElementById('hour').value || 0);
    const minute = Number(document.getElementById('minute').value || 0);
    const second = Number(document.getElementById('second').value || 0);
    const timeConfidence = birthTimeConfidenceForForm();
    let startTime = document.getElementById('rect-start-time').value || '00:00:00';
    let endTime = document.getElementById('rect-end-time').value || '02:00:00';
    if (timeConfidence === 'known' && startTime === '00:00:00' && endTime === '02:00:00') {
        const birthMinutes = hour * 60 + minute;
        startTime = hhmmFromMinutes(birthMinutes - 60);
        endTime = hhmmFromMinutes(birthMinutes + 60);
    }
    const expectedLagna = timeConfidence === 'known'
        && lastChartData
        && lastChartData.lagna
        && chartBirthMatchesCurrentForm(lastChartData)
        ? {
            expected_lagna_sign_index: lastChartData.lagna.sign_index,
            expected_lagna_sign: lastChartData.lagna.sign,
            expected_lagna_sign_tr: lastChartData.lagna.sign_tr
        }
        : {};

    const judgementDateField = document.getElementById('rect-judgement-date');
    const judgementTimeField = document.getElementById('rect-judgement-time');
    const judgementDate = judgementDateField && judgementDateField.value ? judgementDateField.value : localISODate();
    const judgementTime = judgementTimeField && judgementTimeField.value ? judgementTimeField.value : localHHMM();
    const judgementSource = judgementDateField && judgementDateField.value
        ? 'user_supplied'
        : 'auto_generated_browser_analysis_time_birth_location';

    return {
            birth_base: {
                year: document.getElementById('year').value,
                month: document.getElementById('month').value,
                day: document.getElementById('day').value,
                hour,
                minute,
                second,
                tz_offset: document.getElementById('tz_offset').value,
                timezone_id: selectedCityTimezoneId() || undefined,
            ...birthCoordinatePayload(),
            place: selectedBirthPlaceLabel(),
            birth_sex: document.getElementById('birth-sex').value || undefined,
            time_confidence: timeConfidence,
            ...expectedLagna
        },
        search_window: {
            start_time: startTime,
            end_time: endTime,
            step_minutes: Number(document.getElementById('rect-step-minutes').value || 0),
            step_seconds: Number(document.getElementById('rect-step-seconds').value || 0)
        },
        judgement: {
            date: judgementDate,
            time: judgementTime,
            tz_offset: document.getElementById('tz_offset').value,
            timezone_id: selectedCityTimezoneId() || undefined,
            ...birthCoordinatePayload(),
            source: judgementSource
        },
        events
    };
}

function renderRectificationResult(data) {
    const container = document.getElementById('rectification-result');
    if (!container) return;
    lastRectificationDecision = data.rectification_decision || null;
    const rectifiedTimeInput = document.getElementById('rectified-time');
    const productStatus = lastRectificationDecision
        ? (lastRectificationDecision.product_status || {})
        : {};
    if (
        rectifiedTimeInput
        && lastRectificationDecision
        && productStatus.can_save_rectified_time === true
        && (productStatus.suggested_time || lastRectificationDecision.suggested_time)
    ) {
        rectifiedTimeInput.value = normalizeRectificationTimeLabel(
            productStatus.suggested_time || lastRectificationDecision.suggested_time
        );
    }

    const windowRows = (data.candidate_windows || []).map(window => `
        <tr>
            <td>${escapeHTML(window.start_time)}</td>
            <td>${escapeHTML(window.end_time)}</td>
            <td>${escapeHTML(window.candidate_count)}</td>
            <td>${escapeHTML(window.max_score)}</td>
        </tr>
    `).join('');
    const eventMatrixRows = data.event_evidence_matrix && Array.isArray(data.event_evidence_matrix.rows)
        ? data.event_evidence_matrix.rows.map(row => {
            const best = (row.candidate_scores || []).slice().sort((a, b) => b.score - a.score)[0];
            return `
                <tr>
                    <td>${escapeHTML(row.event_type)}</td>
                    <td>${escapeHTML(row.date)}</td>
                    <td>${escapeHTML(row.confidence)}</td>
                    <td>${escapeHTML(row.certainty)}</td>
                    <td>${escapeHTML(best ? best.time : '-')}</td>
                    <td>${escapeHTML(best ? best.score : '-')}</td>
                </tr>
            `;
        }).join('')
        : '';
    const kpRows = data.kp_evidence && Array.isArray(data.kp_evidence.candidate_scores)
        ? data.kp_evidence.candidate_scores.slice(0, 10).map(row => `
            <tr>
                <td>${escapeHTML(row.time)}</td>
                <td>${escapeHTML(row.score)}</td>
                <td>${escapeHTML((row.matches || []).filter(match => match.matches_judgement_ruling_planets).map(match => `${match.role}: ${match.planet}`).join(', ') || '-')}</td>
            </tr>
        `).join('')
        : '';
    const tattwaRows = data.tattwa_evidence && Array.isArray(data.tattwa_evidence.candidate_scores)
        ? data.tattwa_evidence.candidate_scores.slice(0, 10).map(row => `
            <tr>
                <td>${escapeHTML(row.time)}</td>
                <td>${escapeHTML(row.score)}</td>
                <td>${escapeHTML(row.tattwa || '-')}</td>
                <td>${escapeHTML(row.sex_match)}</td>
            </tr>
        `).join('')
        : '';
    const vargaRows = data.varga_evidence && Array.isArray(data.varga_evidence.rows)
        ? data.varga_evidence.rows.slice(0, 15).map(row => `
            <tr>
                <td>${escapeHTML(row.time)}</td>
                <td>${escapeHTML(row.rank || '-')}</td>
                <td>${escapeHTML(signLabel(row.lagna))}</td>
                <td>${escapeHTML(signLabel(row.d9_lagna))}</td>
                <td>${escapeHTML(signLabel(row.d10_lagna))}</td>
                <td>${escapeHTML(signLabel(row.d60_lagna))}</td>
                <td>${escapeHTML(row.change_count)}</td>
            </tr>
        `).join('')
        : '';
    const scoreV1 = data.rectification_score_v1 || {};
    const scoreV1LayerRows = Array.isArray(scoreV1.used_layers)
        ? scoreV1.used_layers.map(row => `
            <tr>
                <td>${escapeHTML(row.key)}</td>
                <td>${escapeHTML(row.score)}</td>
                <td>${escapeHTML(row.used_for_candidate_ranking)}</td>
            </tr>
        `).join('')
        : '';
    const scoreV1Excluded = Array.isArray(scoreV1.excluded_from_score)
        ? scoreV1.excluded_from_score.join(', ')
        : '';

    const topRows = (data.top_candidates || []).map(candidate => `
        <tr>
            <td>${escapeHTML(candidate.rank)}</td>
            <td>${escapeHTML(candidate.time)}</td>
            <td>${escapeHTML(candidate.total_score)}</td>
            <td>${escapeHTML(candidate.ranking_score)}</td>
            <td>${escapeHTML(candidate.layer_scores ? candidate.layer_scores.events : '-')}</td>
            <td>${escapeHTML(candidate.layer_scores ? candidate.layer_scores.kp : '-')}</td>
            <td>${escapeHTML(candidate.layer_scores ? candidate.layer_scores.tattwa : '-')}</td>
            <td>${escapeHTML(signLabel(candidate.lagna))}</td>
            <td>${escapeHTML(candidate.lagna_anchor ? candidate.lagna_anchor.status : '-')}</td>
            <td>${escapeHTML(signLabel(candidate.d9_lagna))}</td>
            <td>${escapeHTML(signLabel(candidate.d10_lagna))}</td>
            <td>${escapeHTML(candidate.kp_lagna_cusp ? candidate.kp_lagna_cusp.sub_lord : '-')}</td>
            <td>${escapeHTML(candidate.kp_lagna_cusp ? candidate.kp_lagna_cusp.sub_sub_lord : '-')}</td>
        </tr>
    `).join('');

    const allRows = (data.candidates || []).slice(0, 40).map(candidate => {
        const eventBrief = (candidate.event_scores || [])
            .map(event => `${event.topic || event.event_type}: ${event.score}`)
            .join(', ');
        return `
            <tr>
                <td>${escapeHTML(candidate.rank)}</td>
                <td>${escapeHTML(candidate.time)}</td>
                <td>${escapeHTML(candidate.total_score)}</td>
                <td>${escapeHTML(candidate.ranking_score)}</td>
                <td>${escapeHTML(signLabel(candidate.lagna))}</td>
                <td>${escapeHTML(candidate.lagna_anchor ? candidate.lagna_anchor.status : '-')}</td>
                <td>${escapeHTML(signLabel(candidate.d60_lagna))}</td>
                <td>${escapeHTML(candidate.change_markers_from_previous_candidate.length)}</td>
                <td>${escapeHTML(eventBrief)}</td>
            </tr>
        `;
    }).join('');

    container.innerHTML = `
        ${renderLayerMeta(data)}
        ${renderRectificationDecision(lastRectificationDecision)}
        <div class="layer-summary-strip">
            <div><span>Skor v1</span><strong>${escapeHTML(scoreV1.status || '-')}</strong></div>
            <div><span>Mod</span><strong>${escapeHTML(scoreV1.ranking_mode || '-')}</strong></div>
            <div><span>En İyi Saat</span><strong>${escapeHTML(scoreV1.top_candidate_time || '-')}</strong></div>
            <div><span>En İyi Skor</span><strong>${escapeHTML(scoreV1.top_ranking_score ?? '-')}</strong></div>
            <div><span>Skor Farkı</span><strong>${escapeHTML(scoreV1.score_gap ?? '-')}</strong></div>
            <div><span>Final Saat</span><strong>${escapeHTML(scoreV1.used_for_final_time_selection === true ? 'izinli' : 'kapalı')}</strong></div>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Skor Katmanı</th><th>Skor</th><th>Sıralamada Kullanıldı</th></tr></thead>
                <tbody>${scoreV1LayerRows || '<tr><td colspan="3">Skor v1 katmanı yok</td></tr>'}</tbody>
            </table>
        </div>
        <p class="quality-note">Skor dışı: ${escapeHTML(scoreV1Excluded || '-')}</p>
        <div class="layer-summary-strip">
            <div><span>Aday</span><strong>${escapeHTML(data.candidate_count)}</strong></div>
            <div><span>Olay</span><strong>${escapeHTML(data.input ? data.input.event_count : '-')}</strong></div>
            <div><span>Step</span><strong>${escapeHTML(rectificationStepLabel(data.input ? data.input.search_window : null))}</strong></div>
            <div><span>Güven</span><strong>${escapeHTML(data.confidence)}</strong></div>
            <div><span>Lagna Çapası</span><strong>${escapeHTML(data.lagna_anchor ? data.lagna_anchor.status : '-')}</strong></div>
            <div><span>KP</span><strong>${escapeHTML(data.kp_evidence ? data.kp_evidence.status : '-')}</strong></div>
            <div><span>Tattwa</span><strong>${escapeHTML(data.tattwa_evidence ? data.tattwa_evidence.status : '-')}</strong></div>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Aralık Başlangıç</th><th>Aralık Bitiş</th><th>Aday</th><th>En Yüksek Skor</th></tr></thead>
                <tbody>${windowRows || '<tr><td colspan="4">Güçlü aday aralığı yok</td></tr>'}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Rank</th><th>Saat</th><th>Toplam</th><th>Sıralama</th><th>Olay</th><th>KP</th><th>Tattwa</th><th>Lagna</th><th>Çapa</th><th>D9</th><th>D10</th><th>KP Sub</th><th>KP Sub-Sub</th></tr></thead>
                <tbody>${topRows || '<tr><td colspan="13">Aday yok</td></tr>'}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Rank</th><th>Saat</th><th>Skor</th><th>Sıralama</th><th>Lagna</th><th>Çapa</th><th>D60</th><th>Değişim</th><th>Olay Skorları</th></tr></thead>
                <tbody>${allRows || '<tr><td colspan="9">Aday yok</td></tr>'}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Olay</th><th>Tarih</th><th>Güven</th><th>Netlik</th><th>En Güçlü Saat</th><th>Skor</th></tr></thead>
                <tbody>${eventMatrixRows || '<tr><td colspan="6">Olay kanıt matrisi yok</td></tr>'}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Saat</th><th>KP Skor</th><th>Eşleşen Ruling Planet</th></tr></thead>
                <tbody>${kpRows || `<tr><td colspan="3">${escapeHTML(data.kp_evidence ? data.kp_evidence.reason || 'KP kanıtı yok' : 'KP kanıtı yok')}</td></tr>`}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Saat</th><th>Tattwa Skor</th><th>Tattwa</th><th>Cinsiyet Uyum</th></tr></thead>
                <tbody>${tattwaRows || `<tr><td colspan="4">${escapeHTML(data.tattwa_evidence ? data.tattwa_evidence.reason || 'Tattwa kanıtı yok' : 'Tattwa kanıtı yok')}</td></tr>`}</tbody>
            </table>
        </div>
        <div class="table-wrapper compact-table">
            <table class="data-table">
                <thead><tr><th>Saat</th><th>Rank</th><th>Lagna</th><th>D9</th><th>D10</th><th>D60</th><th>Değişim</th></tr></thead>
                <tbody>${vargaRows || '<tr><td colspan="7">Varga kanıtı yok</td></tr>'}</tbody>
            </table>
        </div>
    `;
}

function renderRectificationError(message) {
    const container = document.getElementById('rectification-result');
    lastRectificationDecision = null;
    if (!container) return;
    container.innerHTML = `<p class="layer-empty">${escapeHTML(message)}</p>`;
}

function rectificationApiUrl(path) {
    return `${RECTIFICATION_API_BASE}${path}`;
}

function rectificationServiceError(error) {
    if (error instanceof TypeError) {
        return 'Rektifikasyon servisi açık görünmüyor. 5051 portundaki ayrı rektifikasyon API servisini başlatıp tekrar dene.';
    }
    return error.message || 'Rektifikasyon servisi yanıt vermedi.';
}

async function runRectificationAnalysis() {
    const button = document.getElementById('btn-rectification-run');
    if (!button) return;

    button.disabled = true;
    renderRectificationError('Rektifikasyon hesaplanıyor...');
    try {
        saveRectificationEventsForCurrentPerson();
        const response = await fetch(rectificationApiUrl('/api/v2/rectification/analyze'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(buildRectificationPayload())
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Rektifikasyon yapılamadı');
        }
        renderRectificationResult(result);
    } catch (err) {
        renderRectificationError(rectificationServiceError(err));
    } finally {
        button.disabled = false;
    }
}

async function saveRectifiedTime() {
    const button = document.getElementById('btn-rectification-save-time');
    const input = document.getElementById('rectified-time');
    if (!button || !input) return;

    const time = input.value;
    if (!/^\d{2}:\d{2}(:\d{2})?$/.test(time)) {
        setVaultStatus('Rektifiye saat HH:MM veya HH:MM:SS formatında olmalı.', 'error');
        return;
    }
    const [hour, minute, second = 0] = time.split(':').map(Number);
    if (hour < 0 || hour > 23 || minute < 0 || minute > 59 || second < 0 || second > 59) {
        setVaultStatus('Rektifiye saat geçersiz.', 'error');
        return;
    }
    const decisionBlockReason = rectificationDecisionSaveBlockReason(lastRectificationDecision, time);
    if (decisionBlockReason) {
        setVaultStatus(decisionBlockReason, 'error');
        return;
    }

    const person = getPersonInfo();
    if (!person.name) {
        setVaultStatus('Önce kişi adı gerekli.', 'error');
        return;
    }

    const events = collectRectificationEvents();

    const currentBirth = activeRectificationRecord && activeRectificationRecord.birth_base
        ? activeRectificationRecord.birth_base
        : {};
    const currentSearchWindow = activeRectificationRecord && activeRectificationRecord.search_window
        ? activeRectificationRecord.search_window
        : {};
    const currentSourceDocs = activeRectificationRecord && Array.isArray(activeRectificationRecord.source_docs)
        ? activeRectificationRecord.source_docs
        : [];
    const rectStartField = document.getElementById('rect-start-time').value;
    const rectEndField = document.getElementById('rect-end-time').value;
    const shouldKeepSavedWindow = currentSearchWindow.start_time
        && currentSearchWindow.start_time !== '00:00:00'
        && rectStartField === '00:00:00'
        && rectEndField === '02:00:00';
    const rectStart = shouldKeepSavedWindow ? currentSearchWindow.start_time : (rectStartField || currentSearchWindow.start_time || undefined);
    const rectEnd = shouldKeepSavedWindow ? currentSearchWindow.end_time : (rectEndField || currentSearchWindow.end_time || undefined);
    const rectStep = Number(
        document.getElementById('rect-step-minutes').value
        || currentSearchWindow.step_minutes
        || 5
    );
    const rectStepSeconds = Number(
        document.getElementById('rect-step-seconds').value
        || currentSearchWindow.step_seconds
        || 0
    );
    const payload = {
        person,
        birth: {
            year: document.getElementById('year').value,
            month: document.getElementById('month').value,
            day: document.getElementById('day').value,
            hour,
            minute,
            second,
            tz_offset: document.getElementById('tz_offset').value || currentBirth.tz_offset,
            timezone_id: selectedCityTimezoneId() || currentBirth.timezone_id || undefined,
            ...birthCoordinatePayload(),
            place: selectedBirthPlaceLabel() || currentBirth.place || '',
            birth_sex: document.getElementById('birth-sex').value || currentBirth.birth_sex || undefined,
            time_confidence: 'rectified'
        },
        search_window: {
            start_time: rectStart,
            end_time: rectEnd,
            step_minutes: rectStep,
            step_seconds: rectStepSeconds
        },
        events,
        source_docs: currentSourceDocs,
        analysis_profile: selectedAnalysisModeProfile(),
        overwrite: true
    };

    button.disabled = true;
    setVaultStatus(`${person.name} rektifiye saati kaydediliyor...`, '');
    try {
        const response = await fetch(rectificationApiUrl('/api/v2/rectification/save'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Rektifiye saat kaydedilemedi');
        }

        document.getElementById('hour').value = String(hour);
        document.getElementById('minute').value = String(minute);
        document.getElementById('second').value = String(second);
        const updatedItem = {
            ...activeRectificationRecord,
            name: result.person.name,
            group: result.person.group,
            source: 'vault',
            source_type: 'person_file',
            has_life_events: true,
            life_events: {
                birth_base: result.birth_base,
                birth_window: result.birth_window,
                source_docs: result.source_docs,
                events: result.events,
                search_window: result.search_window
            },
            has_rectification: true,
            birth_base: result.birth_base,
            birth_window: result.birth_window,
            source_docs: result.source_docs,
            events: result.events,
            search_window: result.search_window,
            paths: result.paths,
            obsidian_links: result.obsidian_links
        };
        activeRectificationRecord = updatedItem;
        const localItems = upsertRecentSaveItem(updatedItem);
        visibleRecentSaves = mergeRecentAndVaultSaves(localItems, visibleRecentSaves.filter(existing => existing.source === 'vault'));
        renderRecentSaves();
        await openRecentSave(0);
        refreshRecentSaves();
        setVaultStatus(`${person.name} rektifiye saati ${time} olarak kaydedildi.`, 'success');
    } catch (err) {
        setVaultStatus(rectificationServiceError(err), 'error');
    } finally {
        button.disabled = false;
    }
}


// ── Form Handling ───────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('chart-form');
    const citySelect = document.getElementById('city-select');
    const errorBox = document.getElementById('error-box');
    const btnCalculate = document.getElementById('btn-calculate');
    const btnSaveVault = document.getElementById('btn-save-vault');
    const btnCopyExpertPackage = document.getElementById('btn-copy-expert-package');
    const btnCopyTransits = document.getElementById('btn-copy-transits');
    const analysisMode = document.getElementById('analysis-mode');
    const btnRectificationRun = document.getElementById('btn-rectification-run');
    const btnRectificationSaveTime = document.getElementById('btn-rectification-save-time');
    const btnRectificationAddEvent = document.getElementById('btn-rectification-add-event');
    const btnOpenRectification = document.getElementById('btn-open-rectification');
    const rectificationEvents = document.getElementById('rectification-events');
    const btnText = btnCalculate.querySelector('.btn-text');
    const btnLoading = btnCalculate.querySelector('.btn-loading');

    bindResultTabs();
    bindVargaTabs();
    bindRecentSaves();
    refreshRecentSaves();
    loadRectificationEventsForCurrentPerson();
    btnSaveVault.disabled = true;
    if (btnCopyExpertPackage) {
        btnCopyExpertPackage.addEventListener('click', copyExpertPackage);
    }
    if (btnOpenRectification) {
        btnOpenRectification.addEventListener('click', openRectificationPanel);
    }
    if (analysisMode) {
        analysisMode.addEventListener('change', () => {
            if (!lastChartData) return;
            renderExpertCopyPackage(lastChartData);
        });
    }
    if (btnCopyTransits) {
        btnCopyTransits.addEventListener('click', copyTransitPackage);
    }
    if (btnRectificationRun) {
        btnRectificationRun.addEventListener('click', runRectificationAnalysis);
    }
    if (btnRectificationSaveTime) {
        btnRectificationSaveTime.addEventListener('click', saveRectifiedTime);
    }
    if (btnRectificationAddEvent) {
        btnRectificationAddEvent.addEventListener('click', () => {
            createRectificationEventRow('career');
            saveRectificationEventsForCurrentPerson();
        });
    }
    if (rectificationEvents) {
        rectificationEvents.addEventListener('click', event => {
            const button = event.target.closest('.rect-event-remove');
            if (!button || !rectificationEvents.contains(button)) return;
            const row = button.closest('.rectification-event-row');
            if (row) {
                row.remove();
                saveRectificationEventsForCurrentPerson();
            }
        });
        rectificationEvents.addEventListener('change', saveRectificationEventsForCurrentPerson);
        rectificationEvents.addEventListener('input', saveRectificationEventsForCurrentPerson);
    }

    ['person-name', 'group-name'].forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('change', loadRectificationEventsForCurrentPerson);
        }
    });

    populateTurkeyBirthPlaces();
    const birthPlaceSearch = document.getElementById('birth-place-search');
    if (birthPlaceSearch) {
        birthPlaceSearch.addEventListener('change', function() {
            const city = findTurkeyBirthPlace(this.value);
            if (city) {
                applyTurkeyBirthPlace(city);
            }
        });
        birthPlaceSearch.addEventListener('input', function() {
            const city = findTurkeyBirthPlace(this.value);
            if (city) {
                applyTurkeyBirthPlace(city);
            } else if (citySelect) {
                citySelect.value = '';
            }
        });
    }
    const panchangaPlace = document.getElementById('panchanga-place');
    if (panchangaPlace) {
        panchangaPlace.addEventListener('change', function() {
            applyPanchangaTurkeyPlace(this.value);
        });
        panchangaPlace.addEventListener('input', function() {
            applyPanchangaTurkeyPlace(this.value);
        });
    }

    // City select → auto-fill coordinates & timezone
    citySelect.addEventListener('change', function() {
        const option = this.selectedOptions ? this.selectedOptions[0] : null;
        if (!option || !option.value) return;
        if (option.dataset.lat && option.dataset.lon) {
            setCoordinateField('lat', 'lat_direction', option.dataset.lat, 'N', 'S');
            setCoordinateField('lon', 'lon_direction', option.dataset.lon, 'E', 'W');
            document.getElementById('tz_offset').value = option.dataset.tz || '3';
            if (birthPlaceSearch) {
                birthPlaceSearch.value = option.dataset.place || option.textContent.trim();
            }
        } else {
            const parts = option.value.split(',');
            setCoordinateField('lat', 'lat_direction', parts[0], 'N', 'S');
            setCoordinateField('lon', 'lon_direction', parts[1], 'E', 'W');
            document.getElementById('tz_offset').value = parts[2];
            if (birthPlaceSearch) {
                birthPlaceSearch.value = option.textContent.trim();
            }
        }
        syncTimezoneOffsetFromSelectedCity();
    });

    ['day', 'month', 'year', 'hour', 'minute', 'second'].forEach(id => {
        const input = document.getElementById(id);
        if (!input) return;
        const handleBirthInputChange = () => {
            if (['hour', 'minute', 'second'].includes(id)) {
                invalidateRectifiedBirthTime();
            }
            syncTimezoneOffsetFromSelectedCity();
        };
        input.addEventListener('change', handleBirthInputChange);
        input.addEventListener('input', handleBirthInputChange);
    });

    // Form submit
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        errorBox.style.display = 'none';
        setVaultStatus('', '');
        btnSaveVault.disabled = true;
        syncTimezoneOffsetFromSelectedCity();

        const person = getPersonInfo();
        let transitRange;
        try {
            transitRange = selectedTransitRange();
        } catch (err) {
            errorBox.textContent = err.message;
            errorBox.style.display = 'block';
            btnSaveVault.disabled = false;
            return;
        }
        const transitDate = transitRange ? transitRange.start_date : '';
        const tzOffset = document.getElementById('tz_offset').value;
        const timezoneId = selectedCityTimezoneId();
        const panchangaReference = panchangaReferenceForForm(timezoneId, tzOffset);

        const payload = {
            person: {
                id: person.name || null,
                name: person.name || null,
                group: person.group
            },
            birth: {
                year: document.getElementById('year').value,
                month: document.getElementById('month').value,
                day: document.getElementById('day').value,
                hour: document.getElementById('hour').value,
                minute: document.getElementById('minute').value,
                second: document.getElementById('second').value,
                tz_offset: tzOffset,
                timezone_id: timezoneId || undefined,
                ...birthCoordinatePayload(),
                place: selectedBirthPlaceLabel(),
                time_confidence: birthTimeConfidenceForForm(),
                rectification_source: rectificationSourceForForm()
            },
            analysis_profile: selectedAnalysisModeProfile(),
            options: {
                ayanamsa: 'Lahiri',
                zodiac: 'sidereal',
                house_system: 'whole_sign',
                node_type: 'true',
                language: 'tr',
                transit_date: transitDate || undefined,
                transit_time: transitDate ? '12:00' : undefined,
                transit_tz_offset: transitDate ? tzOffset : undefined,
                transit_timezone_id: transitDate && timezoneId ? timezoneId : undefined,
                panchanga_reference: panchangaReference,
                include_life_period_analysis: true,
                life_from_age: 1,
                life_to_date: localISODate()
            }
        };

        // Disable button
        btnCalculate.disabled = true;
        btnText.style.display = 'none';
        btnLoading.style.display = 'inline';

        try {
            const resp = await fetch('/api/v2/chart/full', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await readJsonResponse(resp, 'Harita hesaplama cevabı okunamadı');

            if (!resp.ok) {
                throw new Error(data.error || 'Bilinmeyen hata');
            }

            if (!data.life_period_analysis) {
                try {
                    data.life_period_analysis = await fetchLifePeriodAnalysis(person, timezoneId);
                } catch (lifeErr) {
                    data.life_period_analysis = {
                        status: 'not_available',
                        error: lifeErr.message,
                        technical_notes: ['Life period analysis could not be attached to this expert package.']
                    };
                }
            }

            lastChartData = data;
            lastPersonInfo = person;
            renderResults(data);
            btnSaveVault.disabled = false;

        } catch (err) {
            errorBox.textContent = err.message;
            errorBox.style.display = 'block';
            document.getElementById('results').style.display = 'none';
            lastChartData = null;
            lastPersonInfo = null;
        } finally {
            btnCalculate.disabled = false;
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
        }
    });

    btnSaveVault.addEventListener('click', async function() {
        setVaultStatus('', '');
        const person = getPersonInfo();
        if (!lastChartData) {
            setVaultStatus('Önce harita hesapla.', 'error');
            return;
        }
        if (!person.name) {
            setVaultStatus('Kişi adı gerekli.', 'error');
            return;
        }
        const rectifiedSaveBlockReason = vaultRectifiedTimeSaveBlockReason(lastChartData);
        if (rectifiedSaveBlockReason) {
            setVaultStatus(rectifiedSaveBlockReason, 'error');
            return;
        }

        btnSaveVault.disabled = true;
        try {
            applyAnalysisModeToChart(lastChartData);
            const transitRange = selectedTransitRange();
            const resp = await fetch('/api/v2/vault/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    chart: vaultSaveChartPayload(lastChartData),
                    person,
                    analysis_profile: selectedAnalysisModeProfile(),
                    transit_range: transitRange || undefined,
                    overwrite: true
                })
            });
            const result = await resp.json();
            if (!resp.ok) {
                renderVaultSaveError(result);
                return;
            }
            lastPersonInfo = person;
            renderVaultSaveResult(result);
            addRecentSave(result, person);
        } catch (err) {
            setVaultStatus(err.message, 'error');
        } finally {
            btnSaveVault.disabled = false;
        }
    });
});
