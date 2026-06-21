const state = {
  token: localStorage.getItem("smart-home-token") || "",
  dashboard: null,
  message: "",
  error: "",
  activeSection: "overview",
  pendingFocusSection: "",
  selectedRecordingId: null,
};

const app = document.querySelector("#app");
let scrollSyncHandler = null;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(path, { ...options, headers });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "请求失败");
  return payload;
}

function setMessage(message, isError = false) {
  state.message = isError ? "" : message;
  state.error = isError ? message : "";
}

function focusHomeDemoAfterUpdate() {
  state.activeSection = "home-demo";
  state.pendingFocusSection = "home-demo";
}

function focusPendingSection() {
  if (!state.pendingFocusSection) return;
  const sectionId = state.pendingFocusSection;
  state.pendingFocusSection = "";
  requestAnimationFrame(() => {
    const target = document.querySelector(`#section-${sectionId}`);
    if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

function navigationItems(user) {
  const items = [
    ["overview", "监控总览"],
    ["home-demo", "态势 / 控制"],
    ["monitoring", "监控 / 回放"],
    ["alerts", "告警处理"],
    ["devices", "设备明细"],
  ];
  if (user.role === "admin") items.push(["logs", "系统日志"]);
  return items;
}

async function loadDashboard() {
  try {
    state.dashboard = await api("/api/dashboard");
    setMessage("");
    renderApp();
  } catch (error) {
    localStorage.removeItem("smart-home-token");
    state.token = "";
    state.dashboard = null;
    setMessage(error.message, true);
    renderLogin();
  }
}

function renderLogin() {
  app.innerHTML = `
    <main class="login-shell">
      <section class="login-panel">
        <div class="eyebrow">软件工程期末实践</div>
        <h1>全屋智能安防与语音控制系统</h1>
        <p class="muted">登录后可查看多房间监控、处理异常告警、检索录像，并通过语音指令控制设备和场景。</p>
        <form class="login-form" id="login-form">
          <label>用户名
            <input name="username" value="admin" autocomplete="username" />
          </label>
          <label>密码
            <input name="password" type="password" value="Admin@SE2026!" autocomplete="current-password" />
          </label>
          <button class="primary" type="submit">登录系统</button>
          <p class="muted">演示账号：admin/Admin@SE2026!，member/Member@SE2026!，guest/Guest@SE2026!</p>
          ${state.error ? `<div class="error">${escapeHtml(state.error)}</div>` : ""}
        </form>
      </section>
      <section class="login-visual">
        <div class="login-copy">
          <h2>监控、告警、联动、回放</h2>
          <p>面向家庭安全场景，以规则化异常检测和设备联动展示完整的软件工程原型。</p>
        </div>
      </section>
    </main>
  `;
  document.querySelector("#login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const payload = await api("/api/login", {
        method: "POST",
        body: JSON.stringify({
          username: form.get("username"),
          password: form.get("password"),
        }),
      });
      state.token = payload.token;
      localStorage.setItem("smart-home-token", state.token);
      await loadDashboard();
    } catch (error) {
      setMessage(error.message, true);
      renderLogin();
    }
  });
}

function renderApp() {
  const data = state.dashboard;
  const user = data.user;
  app.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar">
        <div class="brand">
          <strong>全屋智能安防</strong>
          <span>Smart Home Console</span>
        </div>
        <nav class="nav-list">
          ${navigationItems(user).map(([id, label]) => `
            <button class="nav-item ${state.activeSection === id ? "active" : ""}" data-section="${id}" type="button">${label}</button>
          `).join("")}
        </nav>
        <div class="user-box">
          <strong>${escapeHtml(user.display_name)}</strong>
          <span>${escapeHtml(user.username)} · ${escapeHtml(user.role)}</span>
          <button class="secondary" id="logout">退出登录</button>
        </div>
      </aside>
      <main class="main">
        <section class="topbar" id="section-overview">
          <div>
            <div class="eyebrow">实时运行态势</div>
            <h1>家庭安全与设备联动工作台</h1>
            <p class="muted">本地原型使用模拟视频流和传感器事件展示全屋智能业务闭环。</p>
          </div>
          <div class="status-chip">系统在线 · ${new Date().toLocaleString()}</div>
        </section>
        ${state.error ? `<div class="error">${escapeHtml(state.error)}</div>` : ""}
        ${state.message ? `<div class="success">${escapeHtml(state.message)}</div>` : ""}
        ${renderKpis(data.stats)}
        ${renderHomeVisual(data, user)}
        <section class="grid two-col" id="section-monitoring" aria-label="监控与回放">
          ${renderCameras(data.devices)}
          ${renderRecordings(data)}
        </section>
        ${renderAlerts(data, user)}
        ${renderDevices(data, user)}
        ${user.role === "admin" ? renderLogs(data.logs) : ""}
      </main>
    </div>
  `;
  bindActions();
  focusPendingSection();
}

function renderKpis(stats) {
  const items = [
    ["房间", stats.roomCount],
    ["设备", stats.deviceCount],
    ["在线", stats.onlineCount],
    ["摄像头", stats.cameraCount],
    ["未处理告警", stats.openAlertCount],
  ];
  return `<section class="grid kpis">${items.map(([label, value]) => `
    <div class="kpi">
      <div class="muted">${label}</div>
      <div class="value">${value}</div>
    </div>
  `).join("")}</section>`;
}

function roomVisualClass(roomName) {
  return {
    "客厅": "living",
    "卧室": "bedroom",
    "主卧": "bedroom",
    "厨房": "kitchen",
    "玄关": "entry",
    "阳台": "balcony",
  }[roomName] || "room";
}

function isDeviceActive(device) {
  return ["online", "active", "on", "locked", "armed", "cooling"].includes(device.status);
}

function roomSummary(roomDevices, alert) {
  if (alert) return alert.message;
  const activeDevices = roomDevices.filter(isDeviceActive).length;
  return `${activeDevices}/${roomDevices.length} 个设备处于工作态`;
}

function roomState(roomDevices, alert) {
  const alarmActive = roomDevices.some((device) => device.type === "alarm" && device.status === "active");
  if (alert || alarmActive) return "alert";
  return roomDevices.some(isDeviceActive) ? "active" : "idle";
}

function roomDeviceByType(roomDevices, type) {
  return roomDevices.find((device) => device.type === type);
}

function roomStatusLabel(stateName) {
  return {
    active: "运行中",
    alert: "告警",
    idle: "待机",
  }[stateName] || "正常";
}

function miniDeviceControl(device, nextStatus, label, canOperate, className = "") {
  if (!device) return "";
  const classes = ["mini-action", className, isDeviceActive(device) ? "active" : ""]
    .filter(Boolean)
    .join(" ");
  if (!canOperate) return `<span class="${classes}">${escapeHtml(label)}</span>`;
  return `<button class="${classes}" data-device="${device.id}" data-status="${nextStatus}" type="button">${escapeHtml(label)}</button>`;
}

function roomMiniVisual(roomClass, status) {
  const camera = `<div class="mini-camera ${status.cameraOn ? "on" : ""}"><span></span></div>`;
  const sensor = `<div class="mini-sensor ${status.sensorArmed ? "armed" : ""}"></div>`;

  if (roomClass === "entry") {
    return `
      <div class="mini-door ${status.lockLocked ? "locked" : "unlocked"}"></div>
      <div class="mini-mat"></div>
      ${camera}
      <div class="mini-lock ${status.lockLocked ? "locked" : "unlocked"}"></div>
    `;
  }

  if (roomClass === "living") {
    return `
      <div class="mini-window"><span></span><span></span></div>
      <div class="mini-lamp ${status.lightOn ? "on" : ""}"></div>
      <div class="mini-sofa"><span></span></div>
      <div class="mini-table"></div>
      ${camera}
      <div class="mini-alert ${status.alarmActive ? "on" : ""}"></div>
    `;
  }

  if (roomClass === "bedroom") {
    return `
      <div class="mini-bed"><span></span></div>
      <div class="mini-side-table"></div>
      <div class="mini-ac ${status.climateOn ? "on" : ""}"><span></span></div>
      ${camera}
    `;
  }

  if (roomClass === "kitchen") {
    return `
      <div class="mini-kitchen-window"><span></span><span></span></div>
      <div class="mini-range-hood"></div>
      <div class="mini-cabinet-row"><span></span><span></span><span></span></div>
      <div class="mini-counter"></div>
      <div class="mini-sink"><span></span></div>
      <div class="mini-faucet"></div>
      <div class="mini-stove"><span></span><span></span></div>
      <div class="mini-smoke ${status.sensorArmed ? "armed" : ""}"></div>
    `;
  }

  if (roomClass === "balcony") {
    return `
      <div class="mini-sliding-door"><span></span><span></span></div>
      <div class="mini-balcony-floor"></div>
      <div class="mini-balcony-rail"><span></span><span></span><span></span><span></span></div>
      <div class="mini-door-sensor ${status.sensorArmed ? "armed" : ""}"></div>
    `;
  }

  return `
    <div class="mini-room-default"></div>
    ${camera}
    ${sensor}
  `;
}

function renderRoomLiveScene(roomDevices, canOperate, roomClass) {
  const light = roomDeviceByType(roomDevices, "light");
  const camera = roomDeviceByType(roomDevices, "camera");
  const alarm = roomDeviceByType(roomDevices, "alarm");
  const lock = roomDeviceByType(roomDevices, "lock");
  const climate = roomDeviceByType(roomDevices, "climate");
  const sensor = roomDeviceByType(roomDevices, "sensor");
  const status = {
    lightOn: light?.status === "on",
    cameraOn: Boolean(camera && camera.status !== "privacy" && camera.online),
    alarmActive: alarm?.status === "active",
    lockLocked: lock?.status === "locked",
    climateOn: climate?.status === "cooling",
    sensorArmed: sensor?.status === "armed",
  };
  const actions = [
    miniDeviceControl(light, status.lightOn ? "off" : "on", status.lightOn ? "关灯" : "开灯", canOperate, "light"),
    miniDeviceControl(camera, status.cameraOn ? "privacy" : "active", status.cameraOn ? "隐私" : "摄像", canOperate, "camera"),
    miniDeviceControl(alarm, status.alarmActive ? "standby" : "active", status.alarmActive ? "待命" : "警报", canOperate, "alarm"),
    miniDeviceControl(lock, status.lockLocked ? "unlocked" : "locked", status.lockLocked ? "解锁" : "上锁", canOperate, "lock"),
    miniDeviceControl(climate, status.climateOn ? "off" : "cooling", status.climateOn ? "关空调" : "制冷", canOperate, "climate"),
    miniDeviceControl(sensor, status.sensorArmed ? "normal" : "armed", status.sensorArmed ? "正常" : "布防", canOperate, "sensor"),
  ].filter(Boolean).join("");

  return `
    <div class="room-live-scene ${roomClass} ${status.lightOn ? "light-on" : ""} ${status.alarmActive ? "alarm-on" : ""}">
      ${roomMiniVisual(roomClass, status)}
    </div>
    <div class="room-actions">
      ${actions || `<span class="mini-action">仅监测</span>`}
    </div>
  `;
}

function renderRoomOverview(data, alertsByRoom, canOperate) {
  return `
    <div class="room-overview" aria-label="全屋实时画面">
      <div class="room-overview-head">
        <div>
          <h3>全屋实时画面</h3>
          <p class="muted">每个房间都有对应的画面和控制按钮，点完就在本房间画面里看状态变化。</p>
        </div>
        <span class="tag info">${data.rooms.length} 个房间</span>
      </div>
      <div class="room-plan-grid">
        ${data.rooms.map((room) => {
          const roomDevices = data.devices.filter((device) => device.room_name === room.name);
          const alert = alertsByRoom.get(room.name);
          const stateName = roomState(roomDevices, alert);
          const roomClass = roomVisualClass(room.name);
          const shownDevices = roomDevices.slice(0, 3);
          return `
            <article class="room-summary-card ${roomClass} ${stateName}">
              <div class="room-topline">
                <strong>${escapeHtml(room.name)}</strong>
                ${alert ? `<span class="tag bad">告警</span>` : `<span class="tag ${stateName === "active" ? "ok" : "info"}">${roomStatusLabel(stateName)}</span>`}
              </div>
              ${renderRoomLiveScene(roomDevices, canOperate, roomClass)}
              <p class="room-note">${escapeHtml(roomSummary(roomDevices, alert))}</p>
              <div class="room-devices">
                ${shownDevices.map((device) => `
                  <span class="mini-device ${isDeviceActive(device) ? "online" : ""}">
                    ${escapeHtml(device.name)}：${escapeHtml(device.status)}
                  </span>
                `).join("")}
              </div>
            </article>
          `;
        }).join("")}
      </div>
    </div>
  `;
}

function renderHomeVisual(data, user) {
  const alertsByRoom = new Map(data.alerts.map((alert) => [alert.room_name, alert]));
  const canOperate = user.role !== "guest";

  return `
    <section class="panel home-demo" id="section-home-demo">
      <div class="panel-head">
        <div>
          <h2>房屋态势与联动控制</h2>
          <p class="muted">左侧看房间状态，右侧放会改变这些状态的控制。</p>
        </div>
        <span class="tag info">可操作</span>
      </div>
      <div class="control-layout">
        ${renderRoomOverview(data, alertsByRoom, canOperate)}
        <aside class="control-rail" aria-label="联动控制">
          ${renderVoiceAndScenes(data, user)}
          ${renderAlertSimulator(data, user)}
        </aside>
      </div>
    </section>
  `;
}

function renderCameras(devices) {
  const cameras = devices.filter((device) => device.type === "camera");
  return `
    <section class="panel" id="section-cameras">
      <div class="panel-head">
        <h2>实时监控</h2>
        <span class="tag ok">低延迟模拟</span>
      </div>
      <div class="grid camera-grid">
        ${cameras.map((camera) => `
          <article class="camera-card">
            <div class="camera-feed"></div>
            <div class="camera-meta">
              <div class="device-title">
                <strong>${escapeHtml(camera.name)}</strong>
                <span class="tag ${camera.status === "privacy" ? "warn" : "ok"}">${escapeHtml(camera.status)}</span>
              </div>
              <p class="muted">${escapeHtml(camera.room_name)} · ${escapeHtml(camera.metadata.angle || "fixed")}</p>
            </div>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function renderVoiceAndScenes(data, user) {
  const canOperate = user.role !== "guest";
  return `
    <section class="control-box" id="section-voice-scenes">
      <div class="control-box-head">
        <h3>语音与场景</h3>
        <span class="tag info">NLP 模拟</span>
      </div>
      ${canOperate ? `<form id="voice-form" class="voice-row">
        <label>语音指令
          <input name="command" placeholder="例如：打开客厅灯 / 启动离家安防 / 模拟厨房烟雾" />
        </label>
        <button class="primary" type="submit">执行</button>
      </form>` : ""}
      <div class="grid scenes" style="margin-top: 14px;">
        ${data.scenes.map((scene) => `
          <article class="scene-card ${scene.is_active ? "active" : ""}">
            <div class="device-title">
              <strong>${escapeHtml(scene.name)}</strong>
              ${scene.is_active ? `<span class="tag ok">当前</span>` : `<span class="tag">待用</span>`}
            </div>
            <p class="muted">${escapeHtml(scene.description)}</p>
            ${canOperate ? `<button class="secondary" data-scene="${scene.id}">启动场景</button>` : ""}
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function renderAlertSimulator(data, user) {
  const canOperate = user.role !== "guest";
  return `
    <section class="control-box">
      <div class="control-box-head">
        <h3>模拟告警</h3>
        <span class="tag bad">联动</span>
      </div>
      ${canOperate ? `<form id="simulate-form" class="simulate-row">
        <label>房间
          <select name="room_id">
            ${data.rooms.map((room) => `<option value="${room.id}">${escapeHtml(room.name)}</option>`).join("")}
          </select>
        </label>
        <label>事件
          <select name="event_type">
            <option value="intrusion">入侵</option>
            <option value="smoke">烟雾</option>
            <option value="fall">跌倒</option>
            <option value="door_open">门窗异常</option>
            <option value="motion">移动检测</option>
          </select>
        </label>
        <button class="danger" type="submit">触发告警</button>
      </form>` : `<p class="muted">访客只读。</p>`}
    </section>
  `;
}

function renderAlerts(data, user) {
  const canOperate = user.role !== "guest";
  return `
    <section class="panel" id="section-alerts">
      <div class="panel-head">
        <h2>告警中心</h2>
        <span class="tag ${data.alerts.length ? "bad" : "ok"}">${data.alerts.length ? "需处理" : "正常"}</span>
      </div>
      <div class="list">
        ${data.alerts.length ? data.alerts.map((alert) => `
          <article class="alert-item ${escapeHtml(alert.severity)}">
            <div class="device-title">
              <strong>${escapeHtml(alert.message)}</strong>
              <span class="tag bad">${escapeHtml(alert.severity)}</span>
            </div>
            <div class="muted">${escapeHtml(alert.room_name)} · ${escapeHtml(alert.triggered_at)}</div>
            ${canOperate ? `<div class="controls">
              <button class="secondary" data-resolve="${alert.id}">确认处理</button>
            </div>` : ""}
          </article>
        `).join("") : `<p class="muted">暂无未处理告警。</p>`}
      </div>
    </section>
  `;
}

function renderRecordings(data) {
  return `
    <section class="panel" id="section-recordings">
      <div class="panel-head">
        <h2>录像回放</h2>
        <span class="tag info">模拟播放</span>
      </div>
      <form id="recording-filter" class="filter-row">
        <label>关键词
          <input name="keyword" placeholder="烟雾、客厅、门窗" />
        </label>
        <button class="secondary" type="submit">检索</button>
      </form>
      ${renderRecordingPlayer(data.recordings)}
      <div class="list" id="recording-list" style="margin-top: 14px;">
        ${recordingItems(data.recordings)}
      </div>
    </section>
  `;
}

function selectedRecording(recordings) {
  if (!recordings.length) return null;
  return recordings.find((recording) => recording.id === state.selectedRecordingId) || recordings[0];
}

function recordingTitle(recording) {
  const roomName = String(recording.room_name || "").trim();
  let title = String(recording.title || "").trim();
  while (roomName && title.startsWith(roomName)) {
    title = title.slice(roomName.length).trimStart();
  }
  title = title
    .replace(/^检测到/, "")
    .replace(/。片段$/, "片段")
    .replace(/。$/, "");
  return title;
}

function playbackProgress(recording) {
  const duration = Number(recording.duration_seconds || 0);
  return Math.max(24, Math.min(86, 24 + (duration % 64)));
}

function renderRecordingPlayer(recordings) {
  const recording = selectedRecording(recordings);
  if (!recording) {
    return `<div class="recording-player empty" id="recording-player">暂无可回放录像。</div>`;
  }

  return `
    <div class="recording-player" id="recording-player">
      <div class="playback-screen ${escapeHtml(recording.event_type)}">
        <div class="playback-osd">
          <span>PLAYBACK</span>
          <span>${escapeHtml(recording.started_at)}</span>
        </div>
        <div class="playback-scan"></div>
        <div class="playback-target"></div>
        <div class="playback-controls">
          <button class="play-toggle" type="button" aria-label="模拟播放">▶</button>
          <div class="playback-progress"><span style="width: ${playbackProgress(recording)}%;"></span></div>
          <span>${recording.duration_seconds}s</span>
        </div>
      </div>
      <div class="playback-detail">
        <h3>${escapeHtml(recordingTitle(recording))}</h3>
        <div class="recording-meta">
          <span>房间：${escapeHtml(recording.room_name)}</span>
          <span>类型：${escapeHtml(recording.event_type)}</span>
          <span>时长：${recording.duration_seconds}s</span>
        </div>
        <p>${escapeHtml(recording.summary)}</p>
      </div>
    </div>
  `;
}

function recordingItems(recordings) {
  const activeRecording = selectedRecording(recordings);
  const activeId = activeRecording?.id;
  return recordings.map((recording) => `
    <article class="recording-item ${recording.id === activeId ? "active" : ""}">
      <div class="device-title">
        <strong>${escapeHtml(recordingTitle(recording))}</strong>
        <span class="tag info">${escapeHtml(recording.event_type)}</span>
      </div>
      <div class="recording-meta">
        <span>房间：${escapeHtml(recording.room_name)}</span>
        <span>时间：${escapeHtml(recording.started_at)}</span>
        <span>时长：${recording.duration_seconds}s</span>
      </div>
      <p>${escapeHtml(recording.summary)}</p>
      <div class="controls">
        <button class="secondary" data-playback="${recording.id}" type="button">${recording.id === activeId ? "正在播放" : "播放"}</button>
      </div>
    </article>
  `).join("") || `<p class="muted">没有匹配的录像。</p>`;
}

function renderDevices(data, user) {
  const canOperate = user.role !== "guest";
  return `
    <section class="panel" id="section-devices">
      <div class="panel-head">
        <h2>设备控制</h2>
        <span class="tag ok">${data.stats.onlineCount}/${data.stats.deviceCount} 在线</span>
      </div>
      <div class="grid devices">
        ${data.devices.map((device) => `
          <article class="device-card">
            <div class="device-title">
              <strong>${escapeHtml(device.name)}</strong>
              <span class="tag ${device.online ? "ok" : "bad"}">${device.online ? "online" : "offline"}</span>
            </div>
            <div class="muted">${escapeHtml(device.room_name)} · ${escapeHtml(device.type)} · 电量 ${device.battery}%</div>
            <div>当前状态：<strong>${escapeHtml(device.status)}</strong></div>
            ${canOperate ? deviceControl(device) : ""}
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function deviceControl(device) {
  const controls = {
    light: [["on", "开灯"], ["off", "关灯"]],
    climate: [["cooling", "制冷"], ["off", "关闭"]],
    camera: [["active", "启用"], ["privacy", "隐私"]],
    alarm: [["active", "启动"], ["standby", "待命"]],
    lock: [["locked", "上锁"], ["unlocked", "解锁"]],
    sensor: [["armed", "布防"], ["normal", "正常"]],
  }[device.type] || [["active", "启用"], ["off", "关闭"]];
  return `<div class="controls">${controls.map(([status, label]) => `
    <button class="secondary" data-device="${device.id}" data-status="${status}">${label}</button>
  `).join("")}</div>`;
}

function renderLogs(logs) {
  return `
    <section class="panel" id="section-logs">
      <div class="panel-head">
        <h2>审计日志</h2>
        <span class="tag">管理员可见</span>
      </div>
      <div class="list">
        ${logs.map((log) => `
          <article class="log-item">
            <strong>${escapeHtml(log.action)} · ${escapeHtml(log.target_type)}</strong>
            <div class="muted">${escapeHtml(log.created_at)} · ${escapeHtml(log.user_name || "system")}</div>
            <div>${escapeHtml(log.detail)}</div>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function activateRecordingPlayback(recordings, recordingId) {
  state.selectedRecordingId = Number(recordingId);
  const player = document.querySelector("#recording-player");
  const list = document.querySelector("#recording-list");
  if (player) player.outerHTML = renderRecordingPlayer(recordings);
  if (list) list.innerHTML = recordingItems(recordings);
  bindPlaybackButtons(recordings);
}

function bindPlaybackButtons(recordings) {
  document.querySelectorAll("[data-playback]").forEach((button) => {
    button.addEventListener("click", () => {
      activateRecordingPlayback(recordings, button.dataset.playback);
    });
  });
}

function bindActions() {
  const navButtons = [...document.querySelectorAll("[data-section]")];
  const sectionEntries = navButtons
    .map((button) => ({
      id: button.dataset.section,
      button,
      target: document.querySelector(`#section-${button.dataset.section}`),
    }))
    .filter((entry) => entry.target);

  function setActiveSection(sectionId) {
    state.activeSection = sectionId;
    navButtons.forEach((item) => {
      item.classList.toggle("active", item.dataset.section === sectionId);
    });
  }

  function syncActiveSection() {
    const anchorTop = 140;
    const current = sectionEntries
      .map((entry) => ({
        ...entry,
        distance: Math.abs(entry.target.getBoundingClientRect().top - anchorTop),
      }))
      .sort((left, right) => left.distance - right.distance)[0] || sectionEntries[0];
    if (current && current.id !== state.activeSection) {
      setActiveSection(current.id);
    }
  }

  document.querySelectorAll("[data-section]").forEach((button) => {
    button.addEventListener("click", () => {
      const sectionId = button.dataset.section;
      const target = document.querySelector(`#section-${sectionId}`);
      if (!target) return;
      setActiveSection(sectionId);
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  if (scrollSyncHandler) {
    window.removeEventListener("scroll", scrollSyncHandler);
  }
  scrollSyncHandler = syncActiveSection;
  window.addEventListener("scroll", scrollSyncHandler, { passive: true });
  syncActiveSection();
  bindPlaybackButtons(state.dashboard?.recordings || []);

  document.querySelector("#logout").addEventListener("click", () => {
    localStorage.removeItem("smart-home-token");
    state.token = "";
    state.dashboard = null;
    state.activeSection = "overview";
    renderLogin();
  });

  document.querySelectorAll("[data-device]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await api(`/api/devices/${button.dataset.device}`, {
          method: "PATCH",
          body: JSON.stringify({ status: button.dataset.status }),
        });
        setMessage("设备状态已更新。");
        focusHomeDemoAfterUpdate();
        await loadDashboard();
      } catch (error) {
        setMessage(error.message, true);
        renderApp();
      }
    });
  });

  document.querySelectorAll("[data-scene]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await api(`/api/scenes/${button.dataset.scene}/activate`, { method: "POST" });
        setMessage("场景已启动。");
        focusHomeDemoAfterUpdate();
        await loadDashboard();
      } catch (error) {
        setMessage(error.message, true);
        renderApp();
      }
    });
  });

  document.querySelectorAll("[data-resolve]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await api(`/api/alerts/${button.dataset.resolve}/resolve`, {
          method: "POST",
          body: JSON.stringify({ note: "演示中确认告警，已完成处置。" }),
        });
        setMessage("告警已关闭。");
        focusHomeDemoAfterUpdate();
        await loadDashboard();
      } catch (error) {
        setMessage(error.message, true);
        renderApp();
      }
    });
  });

  document.querySelector("#simulate-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await api("/api/alerts/simulate", {
        method: "POST",
        body: JSON.stringify({
          room_id: Number(form.get("room_id")),
          event_type: form.get("event_type"),
        }),
      });
      setMessage("模拟告警已触发，并执行联动策略。");
      focusHomeDemoAfterUpdate();
      await loadDashboard();
    } catch (error) {
      setMessage(error.message, true);
      renderApp();
    }
  });

  document.querySelector("#voice-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const payload = await api("/api/voice", {
        method: "POST",
        body: JSON.stringify({ command: form.get("command") }),
      });
      setMessage(payload.result.message);
      focusHomeDemoAfterUpdate();
      await loadDashboard();
    } catch (error) {
      setMessage(error.message, true);
      renderApp();
    }
  });

  document.querySelector("#recording-filter").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const keyword = encodeURIComponent(form.get("keyword") || "");
      const payload = await api(`/api/recordings?keyword=${keyword}`);
      state.selectedRecordingId = selectedRecording(payload.recordings)?.id || null;
      document.querySelector("#recording-player").outerHTML = renderRecordingPlayer(payload.recordings);
      document.querySelector("#recording-list").innerHTML = recordingItems(payload.recordings);
      bindPlaybackButtons(payload.recordings);
    } catch (error) {
      setMessage(error.message, true);
      renderApp();
    }
  });
}

if (state.token) {
  loadDashboard();
} else {
  renderLogin();
}
