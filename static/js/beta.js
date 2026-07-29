let betaProfileId = null;
let betaChartId = null;
let betaLastMessageId = null;

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

function escapeHTML(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function fieldValue(id) {
    return document.getElementById(id).value;
}

function populateTurkeyPlaceSelect() {
    const select = document.getElementById('beta-place-select');
    const existing = select.querySelector('optgroup[data-generated="turkey"]');
    if (existing) {
        existing.remove();
    }

    const group = document.createElement('optgroup');
    group.label = 'Türkiye - İl merkezleri';
    group.dataset.generated = 'turkey';
    TURKEY_BIRTH_PLACES.forEach(city => {
        const option = document.createElement('option');
        option.value = city.name;
        option.textContent = `${city.plate} - ${city.name} Merkez`;
        option.dataset.place = `${city.name} Merkez, Türkiye`;
        option.dataset.lat = city.lat;
        option.dataset.lon = city.lon;
        option.dataset.tz = '3';
        group.appendChild(option);
    });
    select.appendChild(group);
}

function normalizePlaceText(value) {
    return String(value || '')
        .trim()
        .toLocaleLowerCase('tr-TR')
        .replace(/\s+/g, ' ');
}

function placeOptions() {
    return Array.from(document.querySelectorAll('#beta-place-select option[data-place]'));
}

function applyPlaceOption(option) {
    if (!option) return;
    document.getElementById('beta-place').value = option.dataset.place || option.textContent.trim();
    document.getElementById('beta-lat').value = option.dataset.lat || '';
    document.getElementById('beta-lon').value = option.dataset.lon || '';
    document.getElementById('beta-tz-offset').value = option.dataset.tz || '';
}

function findPlaceOptionByText(value) {
    const normalized = normalizePlaceText(value);
    if (!normalized) return null;
    return placeOptions().find(option => {
        const labels = [
            option.textContent,
            option.dataset.place,
            option.value,
            `${option.value} merkez`,
            `${option.value} merkez, türkiye`,
            `${option.value}, türkiye`
        ].map(normalizePlaceText);
        return labels.includes(normalized);
    }) || null;
}

function syncPlaceSelectFromManualText() {
    const placeInput = document.getElementById('beta-place');
    const select = document.getElementById('beta-place-select');
    const option = findPlaceOptionByText(placeInput.value);
    if (option) {
        select.value = option.value;
        applyPlaceOption(option);
    } else {
        select.value = '';
    }
}

function markPlaceAsManual() {
    document.getElementById('beta-place-select').value = '';
}

function betaBirthPayload() {
    return {
        year: fieldValue('beta-year'),
        month: fieldValue('beta-month'),
        day: fieldValue('beta-day'),
        hour: fieldValue('beta-hour'),
        minute: fieldValue('beta-minute'),
        tz_offset: fieldValue('beta-tz-offset'),
        lat: fieldValue('beta-lat'),
        lon: fieldValue('beta-lon'),
        place: fieldValue('beta-place'),
        time_confidence: fieldValue('beta-time-confidence')
    };
}

function setBusy(button, busy, label) {
    button.disabled = busy;
    if (label) {
        button.textContent = busy ? 'Bekle...' : label;
    }
}

function appendMessage(kind, html) {
    const list = document.getElementById('beta-messages');
    const message = document.createElement('div');
    message.className = `message ${kind}`;
    message.innerHTML = html;
    list.appendChild(message);
    list.scrollTop = list.scrollHeight;
}

function renderSummary(result) {
    const summary = result.chart_summary || {};
    const birth = summary.birth || {};
    const lagna = summary.lagna || {};
    const usage = result.usage || {};
    const chat = usage.chat || {};
    document.getElementById('beta-summary').innerHTML = `
        <div><strong>Profil:</strong> ${escapeHTML(result.profile?.name || '')}</div>
        <div><strong>Lagna:</strong> ${escapeHTML(lagna.sign_tr || lagna.sign || '')} ${escapeHTML(lagna.degree || '')}</div>
        <div><strong>Doğum:</strong> ${escapeHTML(birth.date || '')} ${escapeHTML(birth.time || '')}</div>
        <div><strong>Soru Limiti:</strong> ${escapeHTML(chat.remaining ?? '')}/${escapeHTML(chat.limit ?? '')}</div>
    `;
}

function factorLabel(factor) {
    const kind = factor.kind || factor.type || 'kanıt';
    const source = factor.source || factor.path || '';
    return `${kind}${source ? ` (${source})` : ''}`;
}

function renderFactorList(items) {
    if (!Array.isArray(items) || items.length === 0) {
        return '<p class="message-meta">Kayıt yok.</p>';
    }
    return `<ul>${items.slice(0, 6).map(item => `<li>${escapeHTML(factorLabel(item))}</li>`).join('')}</ul>`;
}

function renderDasha(activeDasha) {
    const path = activeDasha?.path;
    if (!Array.isArray(path) || path.length === 0) {
        return '<p class="message-meta">Aktif dasha yolu bulunamadı.</p>';
    }
    return `<p>${path.map(escapeHTML).join(' / ')}</p>`;
}

function renderMissing(missing) {
    if (!Array.isArray(missing) || missing.length === 0) {
        return '<p class="message-meta">Bu konu için kritik eksik katman bildirilmedi.</p>';
    }
    return `<ul>${missing.slice(0, 6).map(item => `
        <li>${escapeHTML(item.key || 'missing')} - ${escapeHTML(item.impact || item.reason || '')}</li>
    `).join('')}</ul>`;
}

function renderDraft(result) {
    const packet = result.evidence?.topic_packet || {};
    const supporting = packet.supporting_factors || [];
    const challenging = packet.challenging_factors || [];
    const mixed = packet.mixed_factors || [];
    appendMessage('system', `
        <strong>${escapeHTML(result.topic)} / ${escapeHTML(result.status)}</strong>
        <p class="message-meta">Güven: ${escapeHTML(result.confidence)} · Mesaj: ${escapeHTML(result.message_id)}</p>
        <div class="evidence-grid">
            <div class="evidence-box">
                <h3>Aktif Dasha</h3>
                ${renderDasha(result.evidence?.active_dasha)}
            </div>
            <div class="evidence-box">
                <h3>Destekleyen Kanıt</h3>
                ${renderFactorList(supporting)}
            </div>
            <div class="evidence-box">
                <h3>Zorlayan / Karışık Kanıt</h3>
                ${renderFactorList([...challenging, ...mixed])}
            </div>
            <div class="evidence-box">
                <h3>Eksik Katman</h3>
                ${renderMissing(result.missing)}
            </div>
            <div class="evidence-box">
                <h3>Sonraki Adım</h3>
                <p>${escapeHTML(result.next_action || '')}</p>
            </div>
        </div>
    `);
}

async function postJSON(url, payload) {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || data.status || 'İşlem tamamlanamadı');
    }
    return data;
}

async function saveProfile(event) {
    event.preventDefault();
    const button = document.getElementById('beta-save-profile');
    setBusy(button, true, 'Haritayı Hazırla');
    try {
        const result = await postJSON('/api/v2/beta/profile', {
            person: {
                name: fieldValue('beta-person-name'),
                group: fieldValue('beta-group-name')
            },
            birth: betaBirthPayload()
        });
        betaProfileId = result.profile_id;
        betaChartId = result.chart_id;
        betaLastMessageId = null;
        document.getElementById('beta-send').disabled = false;
        document.getElementById('beta-feedback-good').disabled = true;
        document.getElementById('beta-feedback-bad').disabled = true;
        renderSummary(result);
        appendMessage('system', `<strong>Harita hazır</strong><p>${escapeHTML(result.chart_summary?.lagna?.sign_tr || '')} lagna ile sohbet kanıt paketi hazırlanabilir.</p>`);
    } catch (error) {
        appendMessage('error', `<strong>Profil hatası</strong><p>${escapeHTML(error.message)}</p>`);
    } finally {
        setBusy(button, false, 'Haritayı Hazırla');
    }
}

async function sendQuestion(event) {
    event.preventDefault();
    const question = fieldValue('beta-question').trim();
    if (!question || !betaChartId) return;

    const button = document.getElementById('beta-send');
    setBusy(button, true, 'Kanıt Paketini Getir');
    appendMessage('user', `<strong>Soru</strong><p>${escapeHTML(question)}</p>`);
    try {
        const result = await postJSON('/api/v2/beta/chat/draft', {
            profile_id: betaProfileId,
            chart_id: betaChartId,
            question
        });
        betaLastMessageId = result.message_id;
        document.getElementById('beta-feedback-good').disabled = false;
        document.getElementById('beta-feedback-bad').disabled = false;
        renderDraft(result);
        document.getElementById('beta-question').value = '';
    } catch (error) {
        appendMessage('error', `<strong>Sohbet hatası</strong><p>${escapeHTML(error.message)}</p>`);
    } finally {
        setBusy(button, false, 'Kanıt Paketini Getir');
    }
}

async function sendFeedback(rating) {
    if (!betaLastMessageId) return;
    const button = rating === 'good'
        ? document.getElementById('beta-feedback-good')
        : document.getElementById('beta-feedback-bad');
    setBusy(button, true);
    try {
        await postJSON('/api/v2/beta/feedback', {
            profile_id: betaProfileId,
            message_id: betaLastMessageId,
            rating
        });
        appendMessage('system', `<strong>Geri bildirim kaydedildi</strong><p>${escapeHTML(rating)}</p>`);
    } catch (error) {
        appendMessage('error', `<strong>Feedback hatası</strong><p>${escapeHTML(error.message)}</p>`);
    } finally {
        setBusy(button, false);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    populateTurkeyPlaceSelect();
    const placeSelect = document.getElementById('beta-place-select');
    const placeInput = document.getElementById('beta-place');
    placeSelect.addEventListener('change', () => {
        const option = placeSelect.selectedOptions[0];
        if (option && option.dataset.place) {
            applyPlaceOption(option);
        }
    });
    placeInput.addEventListener('change', syncPlaceSelectFromManualText);
    ['beta-lat', 'beta-lon', 'beta-tz-offset'].forEach(id => {
        document.getElementById(id).addEventListener('input', markPlaceAsManual);
    });
    syncPlaceSelectFromManualText();

    document.getElementById('beta-profile-form').addEventListener('submit', saveProfile);
    document.getElementById('beta-chat-form').addEventListener('submit', sendQuestion);
    document.getElementById('beta-feedback-good').addEventListener('click', () => sendFeedback('good'));
    document.getElementById('beta-feedback-bad').addEventListener('click', () => sendFeedback('missing'));
});
