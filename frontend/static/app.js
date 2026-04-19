let selectedScenario = null;
let currentSessionId = null;
let currentSlotKeys = [];
let nextRoundIndex = 1;
let sessionClosed = true;
let sessionBusy = false;
let sessionReviewLocked = false;
let sessionTerminalEntries = [];
let reviewPending = false;
let reviewAvailable = false;
let reviewContext = null;
let authenticatedUser = null;
let sessionStartedAt = '';
let sessionEndedAt = '';
let sessionTimerInterval = null;
let autoKnownAddressValue = '';
let autoCallStartTimeValue = '';
let faultIssueReferenceCategories = null;
let magnifierPressTimer = null;
let magnifierPointerId = null;
let magnifierActive = false;
let magnifierStartPoint = null;
let magnifierLastPoint = null;
let magnifierCloneNode = null;
let magnifierSuppressClickUntil = 0;
let cursorTrailAnimationId = null;
let cursorTrailVisible = false;
let cursorTrailTarget = { x: -320, y: -320 };
let cursorTrailPosition = { x: -320, y: -320 };
let cursorTrailInitialized = false;
let cursorTrailPoints = [];
let cursorTrailLastTimestamp = 0;
let sessionIdCopyFeedbackTimer = null;

const authGate = document.getElementById('auth-gate');
const appShell = document.getElementById('app-shell');
const authError = document.getElementById('auth-error');
const loginForm = document.getElementById('login-form');
const loginUsername = document.getElementById('login-username');
const loginPassword = document.getElementById('login-password');
const loginPasswordToggle = document.getElementById('login-password-toggle');
const loginPasswordToggleLabel = document.getElementById('login-password-toggle-label');
const loginButton = document.getElementById('login-btn');
const startSessionButton = document.getElementById('start-session-btn');
const authUserName = document.getElementById('auth-user-name');
const authUserMeta = document.getElementById('auth-user-meta');
const knownAddressInput = document.getElementById('known-address');
const generateKnownAddressButton = document.getElementById('generate-known-address-btn');
const clearKnownAddressButton = document.getElementById('clear-known-address-btn');
const callStartTimeInput = document.getElementById('call-start-time');
const generateCallStartTimeButton = document.getElementById('generate-call-start-time-btn');
const callStartTimeError = document.getElementById('call-start-time-error');
const useSessionStartTimeCheckbox = document.getElementById('use-session-start-time');
const reviewModal = document.getElementById('review-modal');
const reviewCloseButton = document.getElementById('review-close-btn');
const reviewToggleButton = document.getElementById('review-toggle-btn');
const reviewSummary = document.getElementById('review-summary');
const reviewErrorFields = document.getElementById('review-error-fields');
const failedFlowStageSelect = document.getElementById('failed-flow-stage');
const reviewNotes = document.getElementById('review-notes');
const reviewPersistCheckbox = document.getElementById('review-persist-to-db');
const reviewSubmitButton = document.getElementById('review-submit-btn');
const terminalScrollRegion = document.getElementById('terminal-scroll-region');
const terminalOutput = document.getElementById('terminal-output');
const addressSlotsContainer = document.getElementById('address-slots-container');
const sessionContextPanel = document.getElementById('session-context-panel');
const sessionContextTitle = document.getElementById('session-context-title');
const sessionContextMode = document.getElementById('session-context-mode');
const sessionContextSummary = document.getElementById('session-context-summary');
const sessionCustomerContainer = document.getElementById('session-customer-container');
const sessionRequestContainer = document.getElementById('session-request-container');
const sessionHiddenContextContainer = document.getElementById('session-hidden-context-container');
const sessionContextDetails = Array.from(document.querySelectorAll('.context-group'));
const sessionTimerPanel = document.getElementById('session-timer-panel');
const sessionStartedAtNode = document.getElementById('session-started-at');
const sessionElapsedTimeNode = document.getElementById('session-elapsed-time');
const sessionEndedAtNode = document.getElementById('session-ended-at');
const sessionIdCopyButton = document.getElementById('session-id-copy-btn');
const issueReferencePopover = document.getElementById('issue-reference-popover');
const issueReferenceList = document.getElementById('issue-reference-list');
const issueReferenceCloseButton = document.getElementById('issue-reference-close-btn');
const cursorTrailCanvas = document.getElementById('cursor-trail-canvas');
const cursorTrailContext = cursorTrailCanvas?.getContext('2d');
const textMagnifier = document.getElementById('text-magnifier');
const textMagnifierViewport = document.getElementById('text-magnifier-viewport');
const PERSONA_HIDDEN_CONTEXT_FIELDS = [
    ['gender', '性别'],
    ['emotion', '当前情绪'],
    ['urgency', '紧急程度'],
    ['prior_attempts', '过往尝试'],
    ['special_constraints', '特殊约束'],
    ['current_call_contactable', '当前来电可联系'],
    ['contact_phone_owner', '联系电话归属'],
    ['contact_phone_owner_spoken_label', '联系电话口语表达'],
];
const ADDRESS_SLOT_FIELDS = [
    ['address_slot_province', '省'],
    ['address_slot_city', '市'],
    ['address_slot_district', '区/县'],
    ['address_slot_town', '街道/乡镇'],
    ['address_slot_road', '道路'],
    ['address_slot_community', '小区/社区/学校/医院/酒店'],
    ['address_slot_landmark', '补充定位点'],
    ['address_slot_building', '楼栋'],
    ['address_slot_unit', '单元'],
    ['address_slot_floor', '楼层'],
    ['address_slot_room', '房间'],
];

const ISSUE_REFERENCE_TRIGGER_PATTERN = /请问.*空气能.*现在是出现了什么问题/;
const MAGNIFIER_LONG_PRESS_MS = 350;
const MAGNIFIER_MOVE_TOLERANCE = 10;
const MAGNIFIER_SCALE = 1.75;
const MAGNIFIER_OFFSET = 24;
const CURSOR_TRAIL_EASE = 0.16;
const CURSOR_TRAIL_SETTLE_DISTANCE = 0.8;
const CURSOR_TRAIL_POINT_SPACING = 5;
const CURSOR_TRAIL_MAX_POINTS = 24;

function formatDisplayTimestamp(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    const second = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

function resizeCursorTrailCanvas() {
    if (!cursorTrailCanvas || !cursorTrailContext) return;
    const dpr = window.devicePixelRatio || 1;
    const width = Math.max(Math.floor(window.innerWidth * dpr), 1);
    const height = Math.max(Math.floor(window.innerHeight * dpr), 1);
    if (cursorTrailCanvas.width === width && cursorTrailCanvas.height === height) return;
    cursorTrailCanvas.width = width;
    cursorTrailCanvas.height = height;
    cursorTrailContext.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function ensureCursorTrailAnimation() {
    if (cursorTrailAnimationId !== null || !cursorTrailContext) return;
    cursorTrailAnimationId = window.requestAnimationFrame(renderCursorTrailFrame);
}

function drawCursorTrail(now) {
    if (!cursorTrailContext || !cursorTrailCanvas) return;
    resizeCursorTrailCanvas();
    cursorTrailContext.clearRect(0, 0, window.innerWidth, window.innerHeight);
    if (cursorTrailPoints.length < 2) return;

    cursorTrailContext.lineCap = 'round';
    cursorTrailContext.lineJoin = 'round';

    for (let index = 1; index < cursorTrailPoints.length; index += 1) {
        const previous = cursorTrailPoints[index - 1];
        const current = cursorTrailPoints[index];
        const progress = index / (cursorTrailPoints.length - 1);
        const alphaBase = (1 - progress) * current.life;
        if (alphaBase <= 0.02) continue;

        const palettes = [
            { width: 4.2, alpha: 0.42, hueShift: 0 },
            { width: 2.4, alpha: 0.72, hueShift: 52 },
            { width: 1.2, alpha: 0.96, hueShift: 124 },
        ];

        palettes.forEach((palette, layerIndex) => {
            const hue = (now * 0.05 + current.hue + palette.hueShift + (index * 9)) % 360;
            cursorTrailContext.strokeStyle = `hsla(${hue}, 98%, ${layerIndex === 2 ? 78 : 68}%, ${alphaBase * palette.alpha})`;
            cursorTrailContext.lineWidth = palette.width * (1 - (progress * 0.45));
            cursorTrailContext.beginPath();
            cursorTrailContext.moveTo(previous.x, previous.y);
            cursorTrailContext.lineTo(current.x, current.y);
            cursorTrailContext.stroke();
        });
    }
}

function renderCursorTrailFrame(timestamp) {
    cursorTrailAnimationId = null;
    const delta = cursorTrailLastTimestamp ? Math.min(timestamp - cursorTrailLastTimestamp, 32) : 16;
    cursorTrailLastTimestamp = timestamp;

    const moveAxis = (current, target) => current + ((target - current) * CURSOR_TRAIL_EASE);
    cursorTrailPosition = {
        x: moveAxis(cursorTrailPosition.x, cursorTrailTarget.x),
        y: moveAxis(cursorTrailPosition.y, cursorTrailTarget.y),
    };

    const lastPoint = cursorTrailPoints[cursorTrailPoints.length - 1];
    if (
        cursorTrailVisible
        && (!lastPoint || Math.hypot(cursorTrailPosition.x - lastPoint.x, cursorTrailPosition.y - lastPoint.y) >= CURSOR_TRAIL_POINT_SPACING)
    ) {
        cursorTrailPoints.push({
            x: cursorTrailPosition.x,
            y: cursorTrailPosition.y,
            life: 1,
            hue: (timestamp * 0.03) % 360,
        });
    }

    const decay = cursorTrailVisible ? 0.045 : 0.09;
    cursorTrailPoints = cursorTrailPoints
        .map((point) => ({ ...point, life: point.life - (decay * (delta / 16)) }))
        .filter((point) => point.life > 0.02)
        .slice(-CURSOR_TRAIL_MAX_POINTS);

    drawCursorTrail(timestamp);

    const distance = Math.hypot(
        cursorTrailTarget.x - cursorTrailPosition.x,
        cursorTrailTarget.y - cursorTrailPosition.y,
    );
    if (cursorTrailVisible || cursorTrailPoints.length > 0 || distance > CURSOR_TRAIL_SETTLE_DISTANCE) {
        ensureCursorTrailAnimation();
    }
}

function updateCursorGlow(event) {
    cursorTrailTarget = { x: event.clientX, y: event.clientY };
    if (!cursorTrailInitialized) {
        cursorTrailPosition = { ...cursorTrailTarget };
        cursorTrailInitialized = true;
    }
    cursorTrailVisible = true;
    ensureCursorTrailAnimation();
}

function hideCursorGlow() {
    cursorTrailVisible = false;
    ensureCursorTrailAnimation();
}

function generateMockCallStartTime() {
    const base = new Date();
    const offsetDays = Math.floor(Math.random() * 14);
    base.setDate(base.getDate() - offsetDays);
    base.setHours(
        Math.floor(Math.random() * 24),
        Math.floor(Math.random() * 60),
        Math.floor(Math.random() * 60),
        0,
    );
    return formatDisplayTimestamp(base);
}

function appendTerminalLine(text, tone = 'system') {
    const normalizedText = String(text || '');
    if (currentSessionId) {
        sessionTerminalEntries.push({
            entry_type: 'message',
            tone,
            text: normalizedText,
        });
        renderTerminalEntries(sessionTerminalEntries);
        return;
    }
    const line = document.createElement('div');
    line.className = `terminal-line ${tone}`;
    line.textContent = normalizedText;
    terminalOutput.appendChild(line);
    terminalScrollRegion.scrollTop = terminalScrollRegion.scrollHeight;
}

function clearElement(element) {
    if (element) element.innerHTML = '';
}

function appendContextItem(container, key, value) {
    if (!container) return;
    const item = document.createElement('div');
    item.className = 'context-item';

    const keyNode = document.createElement('span');
    keyNode.className = 'context-item-key';
    keyNode.textContent = key;

    const valueNode = document.createElement('span');
    valueNode.className = 'context-item-value';
    const normalized = value === null || value === undefined ? '' : String(value).trim();
    valueNode.textContent = normalized || '-';
    if (!normalized) valueNode.classList.add('is-empty');

    item.appendChild(keyNode);
    item.appendChild(valueNode);
    container.appendChild(item);
}

function appendSummaryChip(container, label, value) {
    if (!container) return;
    const chip = document.createElement('div');
    chip.className = 'context-summary-chip';
    chip.innerHTML = `<strong>${label}</strong><span>${value}</span>`;
    container.appendChild(chip);
}

function shouldOfferIssueReference(entry) {
    if (!entry || entry.entry_type !== 'turn') return false;
    if (entry.tone !== 'service') return false;
    return ISSUE_REFERENCE_TRIGGER_PATTERN.test(String(entry.text || '').trim());
}

async function loadFaultIssueReferenceCategories() {
    if (Array.isArray(faultIssueReferenceCategories)) return faultIssueReferenceCategories;
    const data = await apiFetch('/api/reference/fault-issue-categories');
    faultIssueReferenceCategories = Array.isArray(data.categories) ? data.categories : [];
    return faultIssueReferenceCategories;
}

function hideIssueReferencePopover() {
    issueReferencePopover.classList.add('hidden');
    issueReferencePopover.setAttribute('aria-hidden', 'true');
    issueReferencePopover.style.left = '';
    issueReferencePopover.style.top = '';
}

function handleDocumentScroll(event) {
    const scrollTarget = event.target;
    if (scrollTarget instanceof Element && scrollTarget.closest('#issue-reference-popover')) {
        return;
    }
    hideIssueReferencePopover();
    if (magnifierActive && magnifierLastPoint) {
        syncTextMagnifierClone(magnifierLastPoint.x, magnifierLastPoint.y);
    }
}

function renderIssueReferenceList(categories) {
    issueReferenceList.innerHTML = '';
    categories.forEach((category) => {
        const item = document.createElement('div');
        item.className = 'issue-reference-item';
        item.textContent = category;
        issueReferenceList.appendChild(item);
    });
}

async function openIssueReferencePopover(anchorElement) {
    try {
        const categories = await loadFaultIssueReferenceCategories();
        renderIssueReferenceList(categories);
        const rect = anchorElement.getBoundingClientRect();
        const estimatedWidth = Math.min(352, window.innerWidth - 32);
        const desiredLeft = Math.min(rect.right + 12, window.innerWidth - estimatedWidth - 16);
        const top = Math.min(rect.top, window.innerHeight - 320);
        issueReferencePopover.style.left = `${Math.max(16, desiredLeft)}px`;
        issueReferencePopover.style.top = `${Math.max(16, top)}px`;
        issueReferencePopover.classList.remove('hidden');
        issueReferencePopover.setAttribute('aria-hidden', 'false');
    } catch (error) {
        appendTerminalLine(`[系统错误] 加载报修问题参考失败：${error.message}`, 'error');
    }
}

function parseDisplayTimestamp(value) {
    const normalized = String(value || '').trim();
    if (!normalized) return null;
    const match = normalized.match(
        /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})$/,
    );
    if (!match) return null;
    const [, year, month, day, hour, minute, second] = match;
    return new Date(
        Number(year),
        Number(month) - 1,
        Number(day),
        Number(hour),
        Number(minute),
        Number(second),
    );
}

function prefillMockCallStartTime(force = false) {
    const currentValue = callStartTimeInput.value.trim();
    if (!force && currentValue && currentValue !== autoCallStartTimeValue) return;
    autoCallStartTimeValue = generateMockCallStartTime();
    callStartTimeInput.value = autoCallStartTimeValue;
}

function isCallStartTimeValid() {
    if (useSessionStartTimeCheckbox.checked) return true;
    return Boolean(parseDisplayTimestamp(callStartTimeInput.value.trim()));
}

function updateCallStartTimeValidationState() {
    const valid = isCallStartTimeValid();
    const useSessionTime = useSessionStartTimeCheckbox.checked;
    callStartTimeInput.disabled = useSessionTime;
    callStartTimeError.classList.toggle('hidden', valid);
    return valid;
}

function updateStartSessionButtonState() {
    const canStart = Boolean(authenticatedUser)
        && Boolean(selectedScenario)
        && !sessionBusy
        && !reviewPending
        && !isReviewModalVisible()
        && isCallStartTimeValid();
    startSessionButton.disabled = !canStart;
}

function sanitizeCloneElementIds(root) {
    if (!root) return;
    if (root.id) root.removeAttribute('id');
    root.querySelectorAll('[id]').forEach((element) => element.removeAttribute('id'));
}

function syncCloneScrollState(sourceRoot, cloneRoot) {
    if (!sourceRoot || !cloneRoot) return;
    const sourceElements = [sourceRoot, ...sourceRoot.querySelectorAll('*')];
    const cloneElements = [cloneRoot, ...cloneRoot.querySelectorAll('*')];
    const total = Math.min(sourceElements.length, cloneElements.length);
    for (let index = 0; index < total; index += 1) {
        cloneElements[index].scrollTop = sourceElements[index].scrollTop;
        cloneElements[index].scrollLeft = sourceElements[index].scrollLeft;
    }
}

function removeNodesFromClone(root, selectors) {
    if (!root) return;
    selectors.forEach((selector) => {
        root.querySelectorAll(selector).forEach((node) => node.remove());
    });
}

function clearMagnifierPressTimer() {
    if (magnifierPressTimer !== null) {
        window.clearTimeout(magnifierPressTimer);
        magnifierPressTimer = null;
    }
}

function teardownTextMagnifierClone() {
    if (magnifierCloneNode && magnifierCloneNode.parentNode === textMagnifierViewport) {
        textMagnifierViewport.removeChild(magnifierCloneNode);
    }
    magnifierCloneNode = null;
}

function hideTextMagnifier() {
    clearMagnifierPressTimer();
    if (magnifierActive) {
        magnifierSuppressClickUntil = Date.now() + 400;
    }
    magnifierActive = false;
    magnifierPointerId = null;
    magnifierStartPoint = null;
    magnifierLastPoint = null;
    textMagnifier.classList.add('hidden');
    textMagnifier.setAttribute('aria-hidden', 'true');
    teardownTextMagnifierClone();
}

function syncTextMagnifierClone(clientX, clientY) {
    if (!magnifierCloneNode) return;
    const sourceRect = {
        left: 0,
        top: 0,
        width: window.innerWidth,
        height: window.innerHeight,
    };
    const viewportRect = textMagnifierViewport.getBoundingClientRect();
    const visibleX = Math.min(Math.max(clientX - sourceRect.left, 0), sourceRect.width);
    const visibleY = Math.min(Math.max(clientY - sourceRect.top, 0), sourceRect.height);
    syncCloneScrollState(document.body, magnifierCloneNode);
    const translateX = (viewportRect.width / 2) - (visibleX * MAGNIFIER_SCALE);
    const translateY = (viewportRect.height / 2) - (visibleY * MAGNIFIER_SCALE);
    magnifierCloneNode.style.transform = `translate(${translateX}px, ${translateY}px) scale(${MAGNIFIER_SCALE})`;
}

function positionTextMagnifier(clientX, clientY) {
    const lensRect = textMagnifier.getBoundingClientRect();
    const maxLeft = Math.max(window.innerWidth - lensRect.width - 12, 12);
    const maxTop = Math.max(window.innerHeight - lensRect.height - 12, 12);
    const desiredLeft = Math.min(clientX + MAGNIFIER_OFFSET, maxLeft);
    const desiredTop = Math.min(clientY + MAGNIFIER_OFFSET, maxTop);
    textMagnifier.style.left = `${Math.max(12, desiredLeft)}px`;
    textMagnifier.style.top = `${Math.max(12, desiredTop)}px`;
}

function showTextMagnifier(clientX, clientY) {
    teardownTextMagnifierClone();
    const clone = document.body.cloneNode(true);
    sanitizeCloneElementIds(clone);
    removeNodesFromClone(clone, ['script', '.text-magnifier']);
    clone.classList.add('text-magnifier-clone');
    clone.style.width = `${window.innerWidth}px`;
    clone.style.height = `${window.innerHeight}px`;
    clone.style.margin = '0';
    syncCloneScrollState(document.body, clone);
    textMagnifierViewport.appendChild(clone);
    magnifierCloneNode = clone;
    magnifierActive = true;
    textMagnifier.classList.remove('hidden');
    textMagnifier.setAttribute('aria-hidden', 'false');
    positionTextMagnifier(clientX, clientY);
    syncTextMagnifierClone(clientX, clientY);
}

function updateTextMagnifier(clientX, clientY) {
    if (!magnifierActive) return;
    positionTextMagnifier(clientX, clientY);
    syncTextMagnifierClone(clientX, clientY);
}

function isWithinTerminalScrollRegion(clientX, clientY) {
    return clientX >= 0 && clientX <= window.innerWidth && clientY >= 0 && clientY <= window.innerHeight;
}

function shouldEnableTextMagnifier(target) {
    if (!target) return false;
    if (target.closest('#text-magnifier')) return false;
    return true;
}

function beginTextMagnifierPress(event) {
    if (event.button !== 0 || !shouldEnableTextMagnifier(event.target)) return;
    clearMagnifierPressTimer();
    magnifierPointerId = event.pointerId;
    magnifierStartPoint = { x: event.clientX, y: event.clientY };
    magnifierLastPoint = { x: event.clientX, y: event.clientY };
    magnifierPressTimer = window.setTimeout(() => {
        magnifierPressTimer = null;
        if (!magnifierLastPoint || !isWithinTerminalScrollRegion(magnifierLastPoint.x, magnifierLastPoint.y)) return;
        showTextMagnifier(magnifierLastPoint.x, magnifierLastPoint.y);
    }, MAGNIFIER_LONG_PRESS_MS);
}

function trackTextMagnifierPointer(event) {
    if (magnifierPointerId !== event.pointerId) return;
    magnifierLastPoint = { x: event.clientX, y: event.clientY };
    if (magnifierActive) {
        updateTextMagnifier(event.clientX, event.clientY);
        return;
    }
    if (!magnifierStartPoint) return;
    const movedX = event.clientX - magnifierStartPoint.x;
    const movedY = event.clientY - magnifierStartPoint.y;
    if (Math.hypot(movedX, movedY) > MAGNIFIER_MOVE_TOLERANCE) {
        clearMagnifierPressTimer();
        magnifierPointerId = null;
        magnifierStartPoint = null;
        magnifierLastPoint = null;
    }
}

function endTextMagnifierPress(event) {
    if (magnifierPointerId !== null && magnifierPointerId !== event.pointerId) return;
    hideTextMagnifier();
}

async function hydrateKnownAddressPrefill(force = false) {
    if (!authenticatedUser || !selectedScenario) return;
    const currentValue = knownAddressInput.value.trim();
    if (!force && currentValue && currentValue !== autoKnownAddressValue) return;
    const scenarioId = selectedScenario.id;
    try {
        const params = new URLSearchParams({ scenario_id: scenarioId });
        const data = await apiFetch(`/api/mock-known-address?${params.toString()}`);
        if (!selectedScenario || selectedScenario.id !== scenarioId) return;
        autoKnownAddressValue = String(data.known_address || '').trim();
        knownAddressInput.value = autoKnownAddressValue;
    } catch (error) {
        if (authenticatedUser) {
            appendTerminalLine(`[系统错误] 预填已知地址失败：${error.message}`, 'error');
        }
    }
}

function formatElapsedDuration(startValue, endValue = '') {
    const startedAtDate = parseDisplayTimestamp(startValue);
    if (!startedAtDate) return '-';
    const endedAtDate = parseDisplayTimestamp(endValue);
    const referenceDate = endedAtDate || new Date();
    const elapsedMs = Math.max(referenceDate.getTime() - startedAtDate.getTime(), 0);
    const totalSeconds = Math.floor(elapsedMs / 1000);
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    return `${days}天 ${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function stopSessionTimer() {
    if (sessionTimerInterval !== null) {
        window.clearInterval(sessionTimerInterval);
        sessionTimerInterval = null;
    }
}

function refreshSessionTimerDisplay() {
    const hasTiming = Boolean(sessionStartedAt);
    sessionTimerPanel.classList.toggle('hidden', !hasTiming);
    sessionStartedAtNode.textContent = sessionStartedAt || '-';
    sessionEndedAtNode.textContent = sessionEndedAt || '-';
    sessionElapsedTimeNode.textContent = hasTiming
        ? formatElapsedDuration(sessionStartedAt, sessionEndedAt)
        : '-';
}

function syncSessionTimer() {
    stopSessionTimer();
    refreshSessionTimerDisplay();
    if (!sessionStartedAt || sessionEndedAt) return;
    sessionTimerInterval = window.setInterval(refreshSessionTimerDisplay, 1000);
}

function updateSessionContextDensity() {
    if (!sessionContextPanel || sessionContextPanel.classList.contains('hidden')) return;
    const hasOpenGroup = sessionContextDetails.some((detail) => detail.open);
    sessionContextPanel.classList.toggle('is-compact', !hasOpenGroup);
}

function updateSessionContext(scenario, sessionConfig = {}) {
    if (!scenario || !sessionConfig.auto_generate_hidden_settings) {
        sessionContextPanel.classList.add('hidden');
        sessionContextPanel.classList.remove('is-compact');
        sessionContextTitle.textContent = '本次会话设定';
        sessionContextMode.textContent = !scenario ? '未开始' : '未启用';
        clearElement(sessionContextSummary);
        clearElement(sessionCustomerContainer);
        clearElement(sessionRequestContainer);
        clearElement(sessionHiddenContextContainer);
        return;
    }

    sessionContextPanel.classList.remove('hidden');
    sessionContextTitle.textContent = `${scenario.scenario_id} 的会话设定`;
    sessionContextMode.textContent = sessionConfig.auto_generate_hidden_settings
        ? '已启用自动生成隐藏设定'
        : '使用原始/兜底设定';

    clearElement(sessionContextSummary);
    clearElement(sessionCustomerContainer);
    clearElement(sessionRequestContainer);
    clearElement(sessionHiddenContextContainer);

    const customer = scenario.customer || {};
    const request = scenario.request || {};
    const hiddenContext = scenario.hidden_context || {};

    appendSummaryChip(sessionContextSummary, '场景', scenario.scenario_id || '-');
    appendSummaryChip(sessionContextSummary, '诉求类型', request.request_type || '-');
    appendSummaryChip(
        sessionContextSummary,
        '已知地址',
        sessionConfig.known_address ? '前端指定核对地址' : '未指定',
    );
    appendSummaryChip(
        sessionContextSummary,
        '故障描述来源',
        hiddenContext.utterance_reference_source === 'library' ? '参考库' : '纯模型',
    );

    [
        ['full_name', customer.full_name],
        ['surname', customer.surname],
        ['phone', customer.phone],
        ['address', customer.address],
        ['persona', customer.persona],
        ['speech_style', customer.speech_style],
    ].forEach(([key, value]) => appendContextItem(sessionCustomerContainer, key, value));

    [
        ['request_type', request.request_type],
        ['issue', request.issue],
        ['desired_resolution', request.desired_resolution],
        ['availability', request.availability],
    ].forEach(([key, value]) => appendContextItem(sessionRequestContainer, key, value));

    const visiblePersonaFields = PERSONA_HIDDEN_CONTEXT_FIELDS
        .map(([key, label]) => [label, hiddenContext[key]])
        .filter(([, value]) => {
            if (value === null || value === undefined) return false;
            if (typeof value === 'string') return value.trim() !== '';
            return true;
        });

    if (!visiblePersonaFields.length) {
        appendContextItem(sessionHiddenContextContainer, '人设信息', '');
        return;
    }

    visiblePersonaFields.forEach(([label, value]) => {
        const renderedValue = typeof value === 'string' ? value : JSON.stringify(value);
        appendContextItem(sessionHiddenContextContainer, label, renderedValue);
    });
    updateSessionContextDensity();
}

function renderTerminalEntries(entries = []) {
    terminalOutput.innerHTML = '';
    entries.forEach((entry) => {
        const line = document.createElement('div');
        line.className = `terminal-line ${entry.tone || 'system'}`;

        if (entry.entry_type === 'turn') {
            const contentText = `[${entry.round_label}] ${entry.speaker}: ${entry.text}`;
            const canRewind = entry.tone === 'user'
                && Boolean(currentSessionId)
                && !sessionBusy
                && !sessionReviewLocked
                && Number(entry.round_index) > 0;
            if (entry.tone === 'user') {
                const trigger = document.createElement('button');
                trigger.type = 'button';
                trigger.className = 'terminal-turn-trigger';
                trigger.textContent = contentText;
                trigger.title = '删除该用户行及其下方所有内容';
                trigger.dataset.roundIndex = String(entry.round_index || '');
                trigger.dataset.restoreCheckpointIndex = String(
                    Number.isFinite(Number(entry.restore_checkpoint_index))
                        ? Number(entry.restore_checkpoint_index)
                        : Math.max(Number(entry.round_index || 0) - 1, 0),
                );
                trigger.dataset.rewindEnabled = canRewind ? 'true' : 'false';
                trigger.classList.toggle('is-disabled', !canRewind);
                line.classList.add('rewindable');
                line.appendChild(trigger);
            } else if (shouldOfferIssueReference(entry)) {
                const trigger = document.createElement('button');
                trigger.type = 'button';
                trigger.className = 'terminal-reference-trigger';
                trigger.textContent = contentText;
                trigger.dataset.referenceTrigger = 'fault-issue-categories';
                line.appendChild(trigger);
            } else {
                line.textContent = contentText;
            }
        } else {
            line.textContent = entry.text || '';
        }

        terminalOutput.appendChild(line);
    });
    terminalScrollRegion.scrollTop = terminalScrollRegion.scrollHeight;
    if (magnifierActive && magnifierLastPoint) {
        showTextMagnifier(magnifierLastPoint.x, magnifierLastPoint.y);
    }
}

function setSessionStatus(status) {
    const badge = document.getElementById('session-status');
    badge.textContent = status;
    badge.className = `status-badge ${status}`;
}

function setNextRound(roundIndex) {
    nextRoundIndex = roundIndex || 1;
    document.getElementById('round-indicator').textContent = `下一轮: ${currentSessionId ? nextRoundIndex : '-'}`;
    document.getElementById('command-prompt').textContent = `[${nextRoundIndex}] 用户:`;
}

function setSessionIdIndicator(sessionId) {
    const indicator = document.getElementById('session-id-indicator');
    if (!indicator || !sessionIdCopyButton) return;
    const normalized = String(sessionId || '').trim();
    indicator.textContent = normalized || '-';
    sessionIdCopyButton.disabled = !normalized;
    sessionIdCopyButton.title = normalized ? '点击复制完整 Session ID' : '启动会话后可复制 Session ID';
    sessionIdCopyButton.dataset.sessionId = normalized;
    sessionIdCopyButton.dataset.copied = 'false';
    const labelNode = sessionIdCopyButton.querySelector('.session-id-copy-label');
    if (labelNode) labelNode.textContent = 'Session ID';
    if (sessionIdCopyFeedbackTimer !== null) {
        window.clearTimeout(sessionIdCopyFeedbackTimer);
        sessionIdCopyFeedbackTimer = null;
    }
}

async function copyCurrentSessionId() {
    if (!sessionIdCopyButton) return;
    const sessionId = String(sessionIdCopyButton.dataset.sessionId || '').trim();
    if (!sessionId) return;
    try {
        await navigator.clipboard.writeText(sessionId);
    } catch (error) {
        const fallbackInput = document.createElement('textarea');
        fallbackInput.value = sessionId;
        fallbackInput.setAttribute('readonly', 'readonly');
        fallbackInput.style.position = 'absolute';
        fallbackInput.style.left = '-9999px';
        document.body.appendChild(fallbackInput);
        fallbackInput.select();
        document.execCommand('copy');
        document.body.removeChild(fallbackInput);
    }
    const labelNode = sessionIdCopyButton.querySelector('.session-id-copy-label');
    if (labelNode) labelNode.textContent = '已复制';
    sessionIdCopyButton.dataset.copied = 'true';
    if (sessionIdCopyFeedbackTimer !== null) {
        window.clearTimeout(sessionIdCopyFeedbackTimer);
    }
    sessionIdCopyFeedbackTimer = window.setTimeout(() => {
        const currentLabelNode = sessionIdCopyButton.querySelector('.session-id-copy-label');
        if (currentLabelNode) currentLabelNode.textContent = 'Session ID';
        sessionIdCopyButton.dataset.copied = 'false';
        sessionIdCopyFeedbackTimer = null;
    }, 1600);
}

function updateInputAvailability(enabled) {
    const input = document.getElementById('user-input');
    const button = document.getElementById('send-btn');
    const endButton = document.getElementById('end-session-btn');
    const canInteract = enabled
        && !sessionBusy
        && !reviewPending
        && !isReviewModalVisible()
        && Boolean(authenticatedUser)
        && !sessionReviewLocked;
    input.disabled = !canInteract;
    button.disabled = !canInteract;
    endButton.disabled = !currentSessionId || sessionClosed || !authenticatedUser || sessionBusy || sessionReviewLocked;
    if (canInteract) input.focus();
}

function isReviewModalVisible() {
    return !reviewModal.classList.contains('hidden');
}

function hideReviewModal() {
    reviewModal.classList.add('hidden');
    reviewModal.setAttribute('aria-hidden', 'true');
}

function showReviewModal() {
    reviewModal.classList.remove('hidden');
    reviewModal.setAttribute('aria-hidden', 'false');
}

function updateReviewToggleButton() {
    const shouldShow = reviewAvailable && !isReviewModalVisible();
    reviewToggleButton.classList.toggle('hidden', !shouldShow);
    reviewToggleButton.disabled = !shouldShow;
}

function setSessionBusyState(busy) {
    sessionBusy = busy;
    updateInputAvailability(!sessionClosed);
    updateCallStartTimeValidationState();
    updateStartSessionButtonState();
    renderTerminalEntries(sessionTerminalEntries);
}

function resetReviewState() {
    reviewPending = false;
    reviewAvailable = false;
    reviewContext = null;
    hideReviewModal();
    document.querySelectorAll('input[name="review-correctness"]').forEach((input) => {
        input.checked = false;
    });
    reviewErrorFields.classList.add('hidden');
    failedFlowStageSelect.innerHTML = '<option value="">请选择出错流程</option>';
    failedFlowStageSelect.value = '';
    reviewNotes.value = '';
    reviewSubmitButton.disabled = false;
    reviewCloseButton.disabled = false;
    updateReviewToggleButton();
    updateStartSessionButtonState();
}

function selectedCorrectnessValue() {
    return document.querySelector('input[name="review-correctness"]:checked')?.value || '';
}

function syncReviewErrorFields() {
    const isIncorrect = selectedCorrectnessValue() === 'incorrect';
    reviewErrorFields.classList.toggle('hidden', !isIncorrect);
}

function openReviewModal(data, { blocking = true } = {}) {
    if (!data.review_required || !currentSessionId) return;
    reviewPending = blocking;
    reviewAvailable = true;
    reviewContext = data;
    reviewSummary.textContent = data.status === 'completed'
        ? `会话已正常结束。Session ID: ${currentSessionId}。请标记当前测试流程是否正确。`
        : `会话已结束。Session ID: ${currentSessionId}。请标记当前测试流程是否正确，并在有问题时指出出错流程。`;
    failedFlowStageSelect.innerHTML = '<option value="">请选择出错流程</option>';
    (data.review_options || []).forEach((option) => {
        const element = document.createElement('option');
        element.value = option.key;
        element.textContent = option.label;
        failedFlowStageSelect.appendChild(element);
    });
    reviewPersistCheckbox.checked = Boolean(data.persist_to_db_default);
    showReviewModal();
    syncReviewErrorFields();
    updateReviewToggleButton();
}

function prepareOptionalReview(data) {
    if (!data.review_required || !currentSessionId) return;
    reviewPending = false;
    reviewAvailable = true;
    reviewContext = data;
    updateReviewToggleButton();
}

function applySessionView(data) {
    if (!data || !data.session_id) return;

    currentSessionId = data.session_id;
    currentSlotKeys = Object.keys(data.collected_slots || {});
    sessionClosed = Boolean(data.session_closed);
    sessionTerminalEntries = Array.isArray(data.terminal_entries) ? data.terminal_entries : [];
    sessionReviewLocked = false;
    sessionStartedAt = String(data.started_at || '').trim();
    sessionEndedAt = String(data.ended_at || '').trim();

    setSessionStatus(data.status || 'active');
    setSessionIdIndicator(data.session_id);
    setNextRound(data.next_round_index);
    updateScenarioHeader(data.scenario);
    updateSessionContext(data.scenario, data.session_config || {});
    updateInspector(data.collected_slots, data.runtime_state, data.scenario);
    renderTerminalEntries(sessionTerminalEntries);
    hideIssueReferencePopover();
    syncSessionTimer();

    if (sessionClosed) {
        resetReviewState();
        if (data.status === 'transferred') {
            prepareOptionalReview(data);
        } else {
            openReviewModal(data);
        }
    } else {
        resetReviewState();
    }

    updateInputAvailability(!sessionClosed);
}

function updateScenarioHeader(scenario) {
    const title = document.getElementById('current-scenario-title');
    if (!scenario) {
        title.textContent = '请选择场景并启动会话';
        return;
    }
    title.textContent = `${scenario.scenario_id} | ${scenario.product.brand} ${scenario.product.model}`;
}

function updateInspector(slots = {}, state = {}, scenario = null) {
    const slotsCont = document.getElementById('slots-container');
    const stateCont = document.getElementById('state-container');

    if (currentSlotKeys.length === 0) {
        slotsCont.innerHTML = '<p class="terminal-hint">会话开始后显示</p>';
    } else {
        slotsCont.innerHTML = '';
        const callStartTime = String(scenario?.call_start_time || '').trim();
        const callStartTimeItem = document.createElement('div');
        callStartTimeItem.className = 'data-item';
        callStartTimeItem.innerHTML = `
            <span class="data-key">call_start_time</span>
            <span class="data-value ${callStartTime ? 'filled' : ''}">${callStartTime || '-'}</span>
        `;
        slotsCont.appendChild(callStartTimeItem);
        currentSlotKeys.forEach((slot) => {
            const value = slots[slot] || '';
            const item = document.createElement('div');
            item.className = 'data-item';
            item.innerHTML = `
                <span class="data-key">${slot}</span>
                <span class="data-value ${value ? 'filled' : ''}">${value || '-'}</span>
            `;
            slotsCont.appendChild(item);
        });
    }

    const currentAddressCandidate = String(state.address_current_candidate || '').trim();
    const hasAddressState = ADDRESS_SLOT_FIELDS.some(([key]) => {
        const value = state[key];
        return value !== null && value !== undefined && String(value).trim() !== '';
    }) || Boolean(currentAddressCandidate);
    if (!hasAddressState) {
        addressSlotsContainer.innerHTML = '<p class="terminal-hint">地址环节开始后显示</p>';
    } else {
        addressSlotsContainer.innerHTML = '';
        if (currentAddressCandidate) {
            const candidateItem = document.createElement('div');
            candidateItem.className = 'data-item address-slot-item';
            candidateItem.innerHTML = `
                <div class="address-slot-head">
                    <span class="data-key">当前地址候选</span>
                </div>
                <span class="address-slot-candidate">${currentAddressCandidate}</span>
            `;
            addressSlotsContainer.appendChild(candidateItem);
        }

        ADDRESS_SLOT_FIELDS.forEach(([key, label]) => {
            const rawValue = state[key];
            const value = rawValue === null || rawValue === undefined ? '' : String(rawValue).trim();
            const item = document.createElement('div');
            item.className = 'data-item address-slot-item';
            item.innerHTML = `
                <div class="address-slot-head">
                    <span class="data-key">${label}</span>
                </div>
                <span class="data-value ${value ? 'filled' : ''}">${value}</span>
            `;
            addressSlotsContainer.appendChild(item);
        });
    }

    const visibleStateEntries = Object.entries(state).filter(([, value]) => {
        if (value === null || value === false || value === 0 || value === '') return false;
        if (Array.isArray(value) && value.length === 0) return false;
        return true;
    });
    const hiddenStateKeys = new Set([
        'address_current_candidate',
        'address_collected_value',
        'address_slot_province',
        'address_slot_city',
        'address_slot_district',
        'address_slot_town',
        'address_slot_road',
        'address_slot_community',
        'address_slot_building',
        'address_slot_unit',
        'address_slot_floor',
        'address_slot_room',
        'address_slot_landmark',
        'address_missing_required_precision',
    ]);
    const filteredStateEntries = visibleStateEntries.filter(([key]) => !hiddenStateKeys.has(key));

    if (filteredStateEntries.length === 0) {
        stateCont.innerHTML = '<p class="terminal-hint">当前没有活跃运行时状态</p>';
        return;
    }

    stateCont.innerHTML = '';
    filteredStateEntries.forEach(([key, value]) => {
        const item = document.createElement('div');
        item.className = 'data-item state-item';
        item.innerHTML = `
            <span class="data-key">${key}</span>
            <span class="data-value mono">${JSON.stringify(value)}</span>
        `;
        stateCont.appendChild(item);
    });
}

function setAuthError(message = '') {
    authError.textContent = message;
    authError.classList.toggle('hidden', !message);
}

function resetWorkspace() {
    selectedScenario = null;
    currentSessionId = null;
    currentSlotKeys = [];
    sessionClosed = true;
    sessionBusy = false;
    sessionReviewLocked = false;
    sessionTerminalEntries = [];
    sessionStartedAt = '';
    sessionEndedAt = '';
    autoKnownAddressValue = '';
    autoCallStartTimeValue = '';
    stopSessionTimer();
    refreshSessionTimerDisplay();
    hideIssueReferencePopover();
    hideTextMagnifier();
    resetReviewState();
    updateScenarioHeader(null);
    updateSessionContext(null, {});
    updateInspector({}, {});
    setSessionStatus('idle');
    setSessionIdIndicator('');
    setNextRound(1);
    updateInputAvailability(false);
    knownAddressInput.value = '';
    callStartTimeInput.value = '';
    useSessionStartTimeCheckbox.checked = false;
    prefillMockCallStartTime(true);
    updateCallStartTimeValidationState();
    updateStartSessionButtonState();
    document.getElementById('scenario-list').innerHTML = '<div class="terminal-hint">登录后显示场景列表</div>';
    document.getElementById('terminal-output').innerHTML = '';
    document.querySelectorAll('.scenario-item').forEach((item) => item.classList.remove('active'));
}

function applyAuthenticatedState(user) {
    authenticatedUser = user;
    authUserName.textContent = user.display_name || user.username;
    authUserMeta.textContent = `备案账号：${user.username}`;
    authGate.classList.add('hidden');
    appShell.classList.remove('hidden');
    setAuthError('');
    updateCallStartTimeValidationState();
    updateStartSessionButtonState();
}

function applyLoggedOutState(message = '') {
    authenticatedUser = null;
    authUserName.textContent = '未登录';
    authUserMeta.textContent = '只有备案账号可访问测试台。';
    appShell.classList.add('hidden');
    authGate.classList.remove('hidden');
    setPasswordVisibility(false);
    loginPassword.value = '';
    setAuthError(message);
    resetWorkspace();
}

function setPasswordVisibility(visible) {
    loginPassword.type = visible ? 'text' : 'password';
    loginPasswordToggle.classList.toggle('is-visible', visible);
    loginPasswordToggleLabel.textContent = visible ? '隐藏' : '显示';
    loginPasswordToggle.setAttribute('aria-pressed', visible ? 'true' : 'false');
    loginPasswordToggle.setAttribute('aria-label', visible ? '隐藏密码' : '显示密码');
    loginPasswordToggle.title = visible ? '隐藏密码' : '显示密码';
}

function togglePasswordVisibility() {
    setPasswordVisibility(loginPassword.type === 'password');
}

async function safeJson(response) {
    try {
        return await response.json();
    } catch (error) {
        return {};
    }
}

async function apiFetch(url, options = {}) {
    const response = await fetch(url, options);
    const data = await safeJson(response);
    if (response.status === 401) {
        applyLoggedOutState(data.detail || '登录状态已失效，请重新登录。');
        throw new Error(data.detail || '请先登录');
    }
    if (!response.ok) {
        throw new Error(data.detail || '请求失败');
    }
    return data;
}

async function loadScenarios() {
    const list = document.getElementById('scenario-list');
    list.innerHTML = '<div class="terminal-hint">加载中...</div>';
    try {
        const scenarios = await apiFetch('/api/scenarios');
        list.innerHTML = '';

        scenarios.forEach((scenario, index) => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'scenario-item';
            item.innerHTML = `
                <span class="scenario-title">${scenario.product}</span>
                <span class="scenario-meta">${scenario.id}</span>
                <span class="scenario-meta">${scenario.request} | max_turns=${scenario.max_turns}</span>
                <span class="scenario-issue">${scenario.issue}</span>
            `;
            item.onclick = () => selectScenario(scenarios[index], item);
            list.appendChild(item);
        });
    } catch (error) {
        if (authenticatedUser) {
            list.innerHTML = `<div class="terminal-hint error">${error.message}</div>`;
        }
    }
}

function selectScenario(scenario, element) {
    selectedScenario = scenario;
    document.querySelectorAll('.scenario-item').forEach((item) => item.classList.remove('active'));
    element.classList.add('active');
    updateScenarioHeader({
        scenario_id: scenario.id,
        product: { brand: scenario.product.split(' ')[0] || scenario.product, model: scenario.product.replace(/^[^ ]+\s*/, '') },
    });
    prefillMockCallStartTime(false);
    updateCallStartTimeValidationState();
    updateStartSessionButtonState();
    hydrateKnownAddressPrefill(false);
}

async function checkAuth() {
    resetWorkspace();
    const response = await fetch('/api/auth/me');
    const data = await safeJson(response);
    if (!response.ok) {
        applyLoggedOutState('');
        return;
    }

    applyAuthenticatedState(data.user);
    await loadScenarios();
}

async function login(event) {
    event.preventDefault();
    const username = loginUsername.value.trim();
    const password = loginPassword.value;
    if (!username || !password) {
        setAuthError('请输入账号和密码。');
        return;
    }

    loginButton.disabled = true;
    setAuthError('');
    try {
        const data = await apiFetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        applyAuthenticatedState(data.user);
        setPasswordVisibility(false);
        loginPassword.value = '';
        await loadScenarios();
    } catch (error) {
        if (!authenticatedUser) {
            setAuthError(error.message);
        }
    } finally {
        loginButton.disabled = false;
    }
}

async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
    } finally {
        applyLoggedOutState('');
    }
}

async function submitReview() {
    if (!currentSessionId) return;

    const correctness = selectedCorrectnessValue();
    if (!correctness) {
        appendTerminalLine('[系统错误] 请先选择本次流程是否正确。', 'error');
        return;
    }

    const isCorrect = correctness === 'correct';
    const failedFlowStage = failedFlowStageSelect.value;
    if (!isCorrect && !failedFlowStage) {
        appendTerminalLine('[系统错误] 流程错误时必须选择出错流程。', 'error');
        return;
    }

    reviewSubmitButton.disabled = true;
    reviewCloseButton.disabled = true;
    try {
        const data = await apiFetch('/api/session/review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                is_correct: isCorrect,
                failed_flow_stage: failedFlowStage,
                notes: reviewNotes.value,
                persist_to_db: reviewPersistCheckbox.checked,
            }),
        });

        appendTerminalLine(
            data.persisted_to_db
                ? `[系统] 评审已提交，session_id=${data.session_id}，username=${data.username}。数据 ${data.session_id} 已写入数据库。`
                : `[系统] 评审已提交，session_id=${data.session_id}，username=${data.username}，本次数据未写入数据库。`,
            'system',
        );
        sessionReviewLocked = true;
        resetReviewState();
        updateInputAvailability(false);
        renderTerminalEntries(sessionTerminalEntries);
    } catch (error) {
        reviewSubmitButton.disabled = false;
        reviewCloseButton.disabled = false;
        appendTerminalLine(`[系统错误] ${error.message}`, 'error');
    }
}

function dismissReview() {
    if (!reviewAvailable) {
        hideReviewModal();
        updateReviewToggleButton();
        return;
    }

    hideReviewModal();
    updateReviewToggleButton();
    updateStartSessionButtonState();
    appendTerminalLine(
        reviewPending
            ? '[系统] 已关闭评审窗口，可点击“打开评审”继续提交。'
            : '[系统] 已关闭评审窗口，如需提交可点击“打开评审”。',
        'system',
    );
}

function reopenReviewModal() {
    if (!reviewAvailable || !reviewContext) return;
    openReviewModal(reviewContext, { blocking: reviewPending });
}

async function startSession() {
    if (reviewPending) {
        appendTerminalLine('请先完成上一条测试记录的评审；如已关闭弹窗，可点击“打开评审”继续。', 'error');
        return;
    }
    if (!selectedScenario) {
        appendTerminalLine('请先在左侧选择一个场景。', 'error');
        return;
    }

    if (!updateCallStartTimeValidationState()) {
        updateStartSessionButtonState();
        return;
    }
    const payload = {
        scenario_id: selectedScenario.id,
        auto_generate_hidden_settings: document.getElementById('auto-hidden-settings').checked,
        known_address: knownAddressInput.value,
        call_start_time: callStartTimeInput.value.trim(),
        use_session_start_time_as_call_start_time: useSessionStartTimeCheckbox.checked,
        persist_to_db: document.getElementById('persist-to-db').checked,
    };

    const output = document.getElementById('terminal-output');
    output.innerHTML = '';
    appendTerminalLine('正在初始化手工测试会话...', 'system');
    sessionBusy = true;
    updateInputAvailability(false);
    updateStartSessionButtonState();
    let errorMessage = '';

    try {
        const data = await apiFetch('/api/session/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        applySessionView(data);
    } catch (error) {
        currentSessionId = null;
        currentSlotKeys = [];
        sessionClosed = true;
        sessionTerminalEntries = [];
        sessionReviewLocked = false;
        resetReviewState();
        setSessionStatus('error');
        setSessionIdIndicator('');
        setNextRound(1);
        updateInspector({}, {});
        errorMessage = error.message;
    } finally {
        setSessionBusyState(false);
        if (errorMessage) {
            appendTerminalLine(`[系统错误] ${errorMessage}`, 'error');
        }
    }
}

async function forceEndSession() {
    if (!currentSessionId || sessionClosed) return;

    setSessionBusyState(true);
    let errorMessage = '';
    try {
        const data = await apiFetch('/api/session/respond', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: currentSessionId, text: '/quit' }),
        });
        applySessionView(data);
    } catch (error) {
        errorMessage = error.message;
    } finally {
        setSessionBusyState(false);
        if (errorMessage) {
            appendTerminalLine(`[系统错误] ${errorMessage}`, 'error');
        }
    }
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    const rawText = input.value;
    const text = rawText.trim();
    if (!text || !currentSessionId || sessionClosed) return;

    input.value = '';
    setSessionBusyState(true);
    let errorMessage = '';
    try {
        const data = await apiFetch('/api/session/respond', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: currentSessionId, text: rawText }),
        });
        applySessionView(data);
    } catch (error) {
        errorMessage = error.message;
    } finally {
        setSessionBusyState(false);
        if (errorMessage) {
            appendTerminalLine(`[系统错误] ${errorMessage}`, 'error');
        }
    }
}

async function rewindFromUserRound(roundIndex, restoreCheckpointIndex) {
    if (!currentSessionId || sessionBusy || sessionReviewLocked || roundIndex < 1) return;

    setSessionBusyState(true);
    let errorMessage = '';
    try {
        const data = await apiFetch('/api/session/rewind', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                clicked_user_round_index: roundIndex,
                restore_checkpoint_index: restoreCheckpointIndex,
            }),
        });
        applySessionView(data);
    } catch (error) {
        errorMessage = error.message;
        if (errorMessage.includes('评审已提交')) {
            sessionReviewLocked = true;
        }
    } finally {
        setSessionBusyState(false);
        if (sessionReviewLocked) {
            renderTerminalEntries(sessionTerminalEntries);
            updateInputAvailability(false);
        }
        if (errorMessage) {
            appendTerminalLine(`[系统错误] ${errorMessage}`, 'error');
        }
    }
}

loginForm.addEventListener('submit', login);
loginPasswordToggle.addEventListener('click', togglePasswordVisibility);
document.getElementById('logout-btn').onclick = logout;
startSessionButton.onclick = startSession;
document.getElementById('end-session-btn').onclick = forceEndSession;
document.getElementById('send-btn').onclick = sendMessage;
document.getElementById('review-submit-btn').onclick = submitReview;
document.getElementById('review-close-btn').onclick = dismissReview;
document.getElementById('review-toggle-btn').onclick = reopenReviewModal;
sessionIdCopyButton.addEventListener('click', copyCurrentSessionId);
clearKnownAddressButton.addEventListener('click', () => {
    knownAddressInput.value = '';
    autoKnownAddressValue = '';
});
generateKnownAddressButton.addEventListener('click', () => {
    hydrateKnownAddressPrefill(true);
});
generateCallStartTimeButton.addEventListener('click', () => {
    useSessionStartTimeCheckbox.checked = false;
    prefillMockCallStartTime(true);
    updateCallStartTimeValidationState();
    updateStartSessionButtonState();
});
knownAddressInput.addEventListener('input', () => {
    if (knownAddressInput.value.trim() !== autoKnownAddressValue) {
        autoKnownAddressValue = '';
    }
});
callStartTimeInput.addEventListener('input', () => {
    if (callStartTimeInput.value.trim() !== autoCallStartTimeValue) {
        autoCallStartTimeValue = '';
    }
    updateCallStartTimeValidationState();
    updateStartSessionButtonState();
});
useSessionStartTimeCheckbox.addEventListener('change', () => {
    if (useSessionStartTimeCheckbox.checked) {
        callStartTimeInput.value = formatDisplayTimestamp(new Date());
    } else if (!callStartTimeInput.value.trim()) {
        prefillMockCallStartTime(true);
    }
    updateCallStartTimeValidationState();
    updateStartSessionButtonState();
});
document.querySelectorAll('input[name="review-correctness"]').forEach((input) => {
    input.addEventListener('change', syncReviewErrorFields);
});
terminalOutput.addEventListener('click', (event) => {
    if (Date.now() < magnifierSuppressClickUntil) {
        event.preventDefault();
        event.stopPropagation();
        return;
    }
    const referenceButton = event.target.closest('.terminal-reference-trigger');
    if (referenceButton) {
        event.preventDefault();
        event.stopPropagation();
        openIssueReferencePopover(referenceButton);
        return;
    }
    const button = event.target.closest('.terminal-turn-trigger');
    if (!button) return;
    event.preventDefault();
    if (button.dataset.rewindEnabled !== 'true') return;
    const roundIndex = Number(button.dataset.roundIndex || '0');
    const restoreCheckpointIndex = Number(button.dataset.restoreCheckpointIndex || '-1');
    if (!roundIndex) return;
    rewindFromUserRound(roundIndex, restoreCheckpointIndex);
});
issueReferenceCloseButton.addEventListener('click', hideIssueReferencePopover);
document.addEventListener('click', (event) => {
    if (issueReferencePopover.classList.contains('hidden')) return;
    const clickedInsidePopover = event.target.closest('#issue-reference-popover');
    const clickedTrigger = event.target.closest('.terminal-reference-trigger');
    if (!clickedInsidePopover && !clickedTrigger) {
        hideIssueReferencePopover();
    }
});
window.addEventListener('resize', () => {
    hideIssueReferencePopover();
    resizeCursorTrailCanvas();
});
window.addEventListener('pointermove', updateCursorGlow, { passive: true });
window.addEventListener('pointermove', trackTextMagnifierPointer);
window.addEventListener('pointerup', endTextMagnifierPress);
window.addEventListener('pointercancel', endTextMagnifierPress);
window.addEventListener('pointerleave', (event) => {
    if (event.target === document.body || event.target === document.documentElement) {
        endTextMagnifierPress(event);
    }
});
window.addEventListener('blur', hideTextMagnifier);
document.addEventListener('pointerleave', hideCursorGlow, true);
document.addEventListener('pointerout', (event) => {
    if (!event.relatedTarget) {
        hideCursorGlow();
    }
}, true);
document.addEventListener('pointerdown', beginTextMagnifierPress);
document.addEventListener('scroll', handleDocumentScroll, true);

sessionContextDetails.forEach((detail) => {
    detail.addEventListener('toggle', updateSessionContextDensity);
});
document.getElementById('user-input').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
});

setSessionStatus('idle');
setSessionIdIndicator('');
setNextRound(1);
resetReviewState();
setPasswordVisibility(false);
prefillMockCallStartTime(true);
updateCallStartTimeValidationState();
updateStartSessionButtonState();
resizeCursorTrailCanvas();
checkAuth();
