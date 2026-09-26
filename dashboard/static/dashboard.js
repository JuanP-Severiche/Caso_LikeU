(() => {
    const root = document.documentElement;
    const form = document.querySelector('#dashboard-filters');
    if (!form || root.dataset.interactiveReady === '1') return;
    root.dataset.interactiveReady = '1';


    const getFilters = () => ({
        date_from: document.querySelector('#date_from').value,
        date_to: document.querySelector('#date_to').value,
        status: document.querySelector('#status').value,
    });

    const escapeHtml = (value) => String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');

    const queryString = (metric) => {
        const filters = getFilters();
        const params = new URLSearchParams({ name: metric, ...filters });
        return params.toString();
    };

    const setStatus = (metric, state, message) => {
        document.querySelectorAll(`[data-query-state="${metric}"]`).forEach((el) => {
            el.dataset.state = state;
            el.textContent = message;
        });
    };

    const updateSupport = (metric, payload) => {
        if (!payload.query) return;
        document.querySelectorAll(`[data-query-support="${metric}"]`).forEach((support) => {
            const paramsEl = support.querySelector('[data-query-params]');
            const sqlEl = support.querySelector('[data-query-sql]');
            if (paramsEl) paramsEl.textContent = JSON.stringify(payload.query.params || [], null, 0);
            if (sqlEl) sqlEl.textContent = payload.query.sql || '-- Consulta no disponible';
        });
    };

    const animateNumber = (el, value, suffix = '', decimals = 2) => {
        if (!el) return;
        const numeric = Number(value ?? 0);
        const duration = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 500;
        const start = performance.now();
        const render = (now) => {
            const progress = duration === 0 ? 1 : Math.min((now - start) / duration, 1);
            const current = numeric * (1 - Math.pow(1 - progress, 3));
            el.textContent = `${current.toLocaleString('es-CO', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals,
            })}${suffix}`;
            if (progress < 1) requestAnimationFrame(render);
        };
        requestAnimationFrame(render);
    };

    const renderBars = (container, rows, labelKey, valueKey, percentageKey = 'percentage') => {
        if (!container) return;
        container.innerHTML = '';
        if (!rows?.length) {
            container.innerHTML = '<p class="empty">Sin datos disponibles</p>';
            return;
        }
        const max = Math.max(...rows.map((r) => Number(r[valueKey] || 0)), 1);
        rows.forEach((row, index) => {
            const value = Number(row[valueKey] || 0);
            const pct = Number(row[percentageKey] || 0);
            const item = document.createElement('div');
            item.className = 'bar-row live-row';
            item.innerHTML = `
                <div class="bar-label">
                    <span title="${escapeHtml(row[labelKey])}">${escapeHtml(row[labelKey])}</span>
                    <strong>${value.toLocaleString('es-CO')} <small>${pct.toFixed(2)}%</small></strong>
                </div>
                <div class="bar-track"><div class="bar-fill live-fill" style="width:0%"></div></div>`;
            container.appendChild(item);
            requestAnimationFrame(() => {
                setTimeout(() => {
                    item.querySelector('.live-fill').style.width = `${(value / max) * 100}%`;
                }, index * 45);
            });
        });
    };

    const renderFunnel = (rows) => {
        const container = document.querySelector('#chart-funnel');
        if (!container) return;
        container.innerHTML = '';
        rows.forEach((row, index) => {
            const pct = Number(row.percentage || 0);
            const item = document.createElement('div');
            item.className = 'funnel-row live-row';
            item.innerHTML = `
                <div class="funnel-header"><span>${escapeHtml(String(row.status || '').replace(/^./, c => c.toUpperCase()))}</span><strong>${pct.toFixed(2)}%</strong></div>
                <div class="bar-track"><div class="bar-fill live-fill" style="width:0%"></div></div>
                <small>${Number(row.messages || 0).toLocaleString('es-CO')} mensajes</small>`;
            container.appendChild(item);
            requestAnimationFrame(() => setTimeout(() => {
                item.querySelector('.live-fill').style.width = `${pct}%`;
            }, index * 70));
        });
    };

    const renderHourly = (rows) => {
        const container = document.querySelector('#chart-hourly');
        if (!container) return;
        container.innerHTML = '';
        const max = Math.max(...rows.map((r) => Number(r.incoming_messages || 0)), 1);
        rows.forEach((row, index) => {
            const total = Number(row.incoming_messages || 0);
            const hour = Number(row.hour_of_day || 0);
            const item = document.createElement('div');
            item.className = 'hour-item live-hour';
            item.title = `${String(hour).padStart(2, '0')}:00 · ${total} mensajes`;
            item.innerHTML = `
                <div class="hour-number">${total || ''}</div>
                <div class="hour-value" style="height:1.5%"></div>
                <span>${String(hour).padStart(2, '0')}</span>`;
            container.appendChild(item);
            requestAnimationFrame(() => setTimeout(() => {
                item.querySelector('.hour-value').style.height = `${Math.max((total / max) * 100, 1.5)}%`;
            }, index * 22));
        });
    };

    const renderKpis = (data) => {
        const map = [
            ['outgoing_messages', '#kpi-outgoing', '', 0],
            ['failed_pct', '#kpi-failed-pct', '%', 2],
            ['read_pct', '#kpi-read-pct', '%', 2],
            ['delivered_pct', '#kpi-delivered-pct', '%', 2],
            ['avg_sla_minutes', '#kpi-avg-sla', ' min', 2],
            ['median_sla_minutes', '#kpi-median-sla', ' min', 2],
            ['p90_sla_minutes', '#kpi-p90-sla', ' min', 2],
            ['coverage_pct', '#kpi-coverage', '%', 2],
        ];
        map.forEach(([key, selector, suffix, decimals]) => animateNumber(document.querySelector(selector), data[key], suffix, decimals));
        const failedText = document.querySelector('#kpi-failed-messages');
        if (failedText) failedText.textContent = `${Number(data.failed_messages || 0).toLocaleString('es-CO')} mensajes failed`;
        const unanswered = document.querySelector('#kpi-unanswered');
        if (unanswered) unanswered.textContent = `${Number(data.unanswered_messages || 0).toLocaleString('es-CO')} incoming sin acción posterior`;
    };

    const renderSla = (data) => {
        const values = {
            '#sla-avg': `${Number(data.avg_sla_minutes || 0).toFixed(2)} min`,
            '#sla-median': `${Number(data.median_sla_minutes || 0).toFixed(2)} min`,
            '#sla-p90': `${Number(data.p90_sla_minutes || 0).toFixed(2)} min`,
            '#sla-coverage': `${Number(data.coverage_pct || 0).toFixed(2)}%`,
        };
        Object.entries(values).forEach(([selector, value]) => {
            const el = document.querySelector(selector);
            if (el) { el.classList.remove('metric-pop'); void el.offsetWidth; el.textContent = value; el.classList.add('metric-pop'); }
        });
    };

    const liveState = { errors: null, templates: null };

    const updateFinding = () => {
        const error = liveState.errors?.[0];
        const template = liveState.templates?.[0];
        if (error) {
            const pct = document.querySelector('#finding-error-pct');
            const label = document.querySelector('#finding-error-label');
            if (pct) pct.textContent = `${Number(error.percentage || 0).toFixed(2)}%`;
            if (label) label.textContent = String(error.label || 'Sin datos');
        }
        if (template) {
            const pct = document.querySelector('#finding-template-pct');
            const label = document.querySelector('#finding-template-label');
            if (pct) pct.textContent = `${Number(template.percentage || 0).toFixed(2)}%`;
            if (label) label.textContent = String(template.label || 'Sin datos');
        }
    };

    const renderMetric = (metric, data) => {
        if (metric === 'kpis') renderKpis(data);
        else if (metric === 'sla') renderSla(data);
        else if (metric === 'funnel') renderFunnel(data || []);
        else if (metric === 'hourly') renderHourly(data || []);
        else if (metric === 'errors') {
            liveState.errors = data || [];
            renderBars(document.querySelector('#chart-errors'), liveState.errors, 'label', 'total');
            updateFinding();
        }
        else if (metric === 'templates') {
            liveState.templates = data || [];
            renderBars(document.querySelector('#chart-templates'), liveState.templates, 'label', 'total');
            updateFinding();
        }
        else if (metric === 'categories') renderBars(document.querySelector('#chart-categories'), data || [], 'label', 'total');
    };

    const runMetric = async (metric) => {
        setStatus(metric, 'running', 'Ejecutando SQL…');
        document.querySelectorAll(`[data-run="${metric}"]`).forEach((b) => b.disabled = true);
        try {
            const response = await fetch(`/api/query?${queryString(metric)}`, { headers: { 'Accept': 'application/json' } });
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.error || 'Error de consulta');
            renderMetric(metric, payload.data);
            updateSupport(metric, payload);
            setStatus(metric, 'ok', `Ejecutada · ${payload.elapsed_ms.toFixed(2)} ms`);
            return payload;
        } catch (error) {
            setStatus(metric, 'error', error.message || 'Error');
            throw error;
        } finally {
            document.querySelectorAll(`[data-run="${metric}"]`).forEach((b) => b.disabled = false);
        }
    };

    const allMetrics = ['kpis', 'funnel', 'sla', 'hourly', 'errors', 'templates', 'categories'];

    const runAll = async () => {
        const button = document.querySelector('#run-all');
        const banner = document.querySelector('#live-banner');
        if (button) button.disabled = true;
        if (banner) { banner.dataset.state = 'running'; banner.textContent = 'Ejecutando todas las consultas contra PostgreSQL…'; }
        const started = performance.now();
        const results = await Promise.allSettled(allMetrics.map(runMetric));
        const errors = results.filter((r) => r.status === 'rejected').length;
        const elapsed = Math.round(performance.now() - started);
        if (banner) {
            banner.dataset.state = errors ? 'error' : 'ok';
            banner.textContent = errors
                ? `Finalizó con ${errors} consulta(s) con error.`
                : `Análisis actualizado en tiempo real · ${elapsed} ms en navegador`;
        }
        if (button) button.disabled = false;
    };

    form.addEventListener('submit', (event) => {
        event.preventDefault();
        runAll();
    });

    document.querySelectorAll('[data-run]').forEach((button) => {
        button.addEventListener('click', () => runMetric(button.dataset.run));
    });

    const reset = document.querySelector('#reset-live');
    if (reset) reset.addEventListener('click', () => {
        document.querySelector('#date_from').value = '2023-07-25';
        document.querySelector('#date_to').value = '2023-08-02';
        document.querySelector('#status').value = '';
        runAll();
    });

    const demo = document.querySelector('#presentation-mode');
    if (demo) demo.addEventListener('click', async () => {
        demo.disabled = true;
        for (const metric of ['funnel', 'sla', 'hourly', 'errors', 'templates', 'categories']) {
            const target = document.querySelector(`[data-card="${metric}"]`);
            if (target) target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            await runMetric(metric).catch(() => null);
            await new Promise((resolve) => setTimeout(resolve, 650));
        }
        demo.disabled = false;
    });

    const renderPreviewTable = (table, preview) => {
        if (!table) return;
        const columns = preview?.columns || [];
        const rows = preview?.rows || [];
        if (!columns.length || !rows.length) {
            table.innerHTML = '<tbody><tr><td>Sin datos disponibles</td></tr></tbody>';
            return;
        }
        const head = `<thead><tr>${columns.map((column) => `<th>${escapeHtml(column)}</th>`).join('')}</tr></thead>`;
        const body = `<tbody>${rows.map((row) => `<tr>${columns.map((column) => `<td title="${escapeHtml(row[column] || '')}">${escapeHtml(row[column] || '')}</td>`).join('')}</tr>`).join('')}</tbody>`;
        table.innerHTML = head + body;
    };

    const renderFileMeta = (element, file, database) => {
        if (!element) return;
        if (!file?.exists) {
            element.innerHTML = '<span class="file-status missing">No encontrado</span>';
            return;
        }
        const rows = file.rows_on_disk == null ? '—' : Number(file.rows_on_disk).toLocaleString('es-CO');
        const db = database?.records != null ? ` · PostgreSQL: ${Number(database.records).toLocaleString('es-CO')} registros` : '';
        element.innerHTML = `
            <span class="file-status ok">Disponible</span>
            <span><strong>${escapeHtml(file.name)}</strong></span>
            <span>${escapeHtml(file.size || '')}</span>
            <span>${rows} filas${db}</span>
            <span>${escapeHtml(file.modified_at || '')}</span>`;
    };

    const renderPipeline = (steps) => {
        const container = document.querySelector('#etl-pipeline');
        if (!container) return;
        container.innerHTML = (steps || []).map((step, index) => `
            <div class="etl-step">
                <span class="etl-step-number">${Number(step.number || index + 1)}</span>
                <div><strong>${escapeHtml(step.label || '')}</strong><small>${escapeHtml(step.detail || '')}</small></div>
            </div>
            ${index < (steps || []).length - 1 ? '<span class="etl-arrow">→</span>' : ''}`).join('');
    };

    const renderCodeSupport = (items) => {
        const container = document.querySelector('#etl-code-support');
        if (!container) return;
        if (!items?.length) {
            container.innerHTML = '<p class="empty">Sin código de apoyo disponible.</p>';
            return;
        }
        container.innerHTML = items.map((item) => `
            <details class="query-support etl-code-item">
                <summary>
                    <span class="query-summary-left">
                        <span class="query-icon">Py</span>
                        <span><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.description)}</small></span>
                    </span>
                    <span class="query-tag">PYTHON</span>
                </summary>
                <div class="query-body"><pre><code>${escapeHtml(item.code || '')}</code></pre></div>
            </details>`).join('');
    };

    const applyEtlTrace = (payload) => {
        renderPipeline(payload.steps || []);
        renderFileMeta(document.querySelector('#raw-file-meta'), payload.raw, null);
        renderFileMeta(document.querySelector('#processed-file-meta'), payload.processed, payload.database || null);
        renderPreviewTable(document.querySelector('#raw-preview-table'), payload.raw_preview);
        renderPreviewTable(document.querySelector('#processed-preview-table'), payload.processed_preview);
        const quality = payload.text_quality || {};
        const repaired = document.querySelector('#quality-repaired');
        const loss = document.querySelector('#quality-loss');
        const ok = document.querySelector('#quality-ok');
        if (repaired) repaired.textContent = Number(quality.encoding_repaired || 0).toLocaleString('es-CO');
        if (loss) loss.textContent = Number(quality.source_character_loss || 0).toLocaleString('es-CO');
        if (ok) ok.textContent = Number(quality.ok || 0).toLocaleString('es-CO');
        renderCodeSupport(payload.code_support || []);
    };

    const loadEtlTrace = async () => {
        const banner = document.querySelector('#etl-run-state');
        try {
            if (banner) { banner.dataset.state = 'running'; banner.textContent = 'Leyendo evidencia del archivo crudo, salida limpia y código ETL…'; }
            const response = await fetch('/api/etl/trace', { headers: { 'Accept': 'application/json' } });
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.error || 'No fue posible leer la evidencia ETL');
            applyEtlTrace(payload);
            if (banner) {
                banner.dataset.state = 'ok';
                banner.textContent = payload.processed?.exists
                    ? `CSV limpio disponible: ${payload.processed.name} · ${Number(payload.processed.rows_on_disk || 0).toLocaleString('es-CO')} filas.`
                    : 'El archivo de salida todavía no existe. Ejecute el ETL para generarlo.';
            }
        } catch (error) {
            if (banner) { banner.dataset.state = 'error'; banner.textContent = error.message; }
        }
    };

    const runEtlLive = async () => {
        const button = document.querySelector('#run-etl-live');
        const refresh = document.querySelector('#refresh-etl-trace');
        const banner = document.querySelector('#etl-run-state');
        const terminal = document.querySelector('#etl-terminal-panel');
        const log = document.querySelector('#etl-terminal-log code');
        if (button) button.disabled = true;
        if (refresh) refresh.disabled = true;
        if (banner) { banner.dataset.state = 'running'; banner.textContent = 'Ejecutando ETL: lectura → limpieza → JSON → NLP → CSV → PostgreSQL…'; }
        if (terminal) terminal.open = true;
        if (log) log.textContent = 'Ejecutando python -m src.main…';
        try {
            const response = await fetch('/api/etl/run', { method: 'POST', headers: { 'Accept': 'application/json' } });
            const payload = await response.json();
            if (log) log.textContent = payload.log || payload.error || 'Sin salida de log.';
            if (!response.ok || !payload.ok) throw new Error(payload.error || payload.log || 'El ETL terminó con error');
            if (payload.trace) applyEtlTrace({ ...payload.trace, database: payload.database || {} });
            if (banner) { banner.dataset.state = 'ok'; banner.textContent = `ETL finalizado correctamente · ${(Number(payload.elapsed_ms || 0) / 1000).toFixed(2)} s · CSV y PostgreSQL actualizados.`; }
            await runAll();
        } catch (error) {
            if (banner) { banner.dataset.state = 'error'; banner.textContent = 'ETL con error. Revise el log desplegado debajo.'; }
            if (log && !log.textContent) log.textContent = error.message;
        } finally {
            if (button) button.disabled = false;
            if (refresh) refresh.disabled = false;
        }
    };

    const refreshEtl = document.querySelector('#refresh-etl-trace');
    if (refreshEtl) refreshEtl.addEventListener('click', loadEtlTrace);
    const runEtl = document.querySelector('#run-etl-live');
    if (runEtl) runEtl.addEventListener('click', runEtlLive);

    loadEtlTrace();
})();
