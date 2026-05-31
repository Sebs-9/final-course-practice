const state = {
  token: localStorage.getItem("smart-home-token") || "",
  dashboard: null,
  message: "",
  error: "",
  activeSection: "overview",
};

const app = document.querySelector("#app");

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

function navigationItems(user) {
  const items = [
    ["overview", "监控总览"],
    ["home-demo", "房屋态势"],
    ["devices", "设备控制"],
    ["alerts", "告警中心"],
    ["recordings", "录像回放"],
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
            <input name="password" type="password" value="admin123" autocomplete="current-password" />
          </label>
          <button class="primary" type="submit">登录系统</button>
          <p class="muted">演示账号：admin/admin123，member/member123，guest/guest123</p>
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
        <section class="grid two-col">
          ${renderCameras(data.devices)}
          ${renderVoiceAndScenes(data, user)}
        </section>
        <section class="grid two-col">
          ${renderAlerts(data, user)}
          ${renderRecordings(data)}
        </section>
        ${renderDevices(data, user)}
        ${user.role === "admin" ? renderLogs(data.logs) : ""}
      </main>
    </div>
  `;
  bindActions();
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

function livingRoomDevice(devices, type) {
  return devices.find((device) => device.room_name === "客厅" && device.type === type);
}

function livingRoomControl(device, nextStatus, label, canOperate) {
  if (!device) return "";
  if (!canOperate) return `<span class="living-marker">${label}</span>`;
  return `<button class="living-marker" data-device="${device.id}" data-status="${nextStatus}" type="button">${label}</button>`;
}

function renderLivingRoomScene(data, canOperate, alertsByRoom) {
  const livingDevices = data.devices.filter((device) => device.room_name === "客厅");
  const light = livingRoomDevice(data.devices, "light");
  const camera = livingRoomDevice(data.devices, "camera");
  const alarm = livingRoomDevice(data.devices, "alarm");
  const livingAlert = alertsByRoom.get("客厅");
  const lightOn = light?.status === "on";
  const cameraOn = camera && camera.status !== "privacy" && camera.online;
  const alarmActive = alarm?.status === "active";
  const alerting = Boolean(livingAlert || alarmActive);

  return `
    <section class="living-showcase ${lightOn ? "lights-on" : "lights-off"} ${alerting ? "alert" : ""}">
      <div class="living-info">
        <div>
          <div class="eyebrow">客厅实时画面</div>
          <h3>客厅智能场景演示</h3>
          <p class="muted">${livingAlert ? escapeHtml(livingAlert.message) : "点击画面中的设备标记或下方控制按钮，客厅画面会同步变化。"}</p>
        </div>
        <div class="tag-row">
          <span class="tag ${lightOn ? "ok" : "info"}">灯光 ${light?.status || "unknown"}</span>
          <span class="tag ${cameraOn ? "ok" : "warn"}">摄像头 ${camera?.status || "unknown"}</span>
          <span class="tag ${alerting ? "bad" : "info"}">警报 ${alarm?.status || "standby"}</span>
        </div>
      </div>
      <div class="living-room-picture">
        <div class="living-window">
          <span></span><span></span>
        </div>
        <div class="ceiling-light ${lightOn ? "on" : ""}"></div>
        <div class="wall-camera ${cameraOn ? "active" : "privacy"}">
          <span></span>
        </div>
        <div class="air-conditioner">
          <span></span>
        </div>
        <div class="sofa">
          <span class="sofa-back"></span>
          <span class="sofa-seat"></span>
          <span class="sofa-arm left"></span>
          <span class="sofa-arm right"></span>
        </div>
        <div class="coffee-table"></div>
        <div class="floor-rug"></div>
        <div class="alert-beacon ${alerting ? "active" : ""}"></div>
        <div class="living-controls">
          ${livingRoomControl(light, lightOn ? "off" : "on", lightOn ? "关客厅灯" : "开客厅灯", canOperate)}
          ${livingRoomControl(camera, cameraOn ? "privacy" : "active", cameraOn ? "隐私模式" : "开启摄像头", canOperate)}
          ${livingRoomControl(alarm, alarmActive ? "standby" : "active", alarmActive ? "警报待命" : "启动警报", canOperate)}
        </div>
      </div>
      <div class="living-device-strip">
        ${livingDevices.map((device) => `
          <span class="mini-device ${isDeviceActive(device) ? "online" : ""}">
            ${escapeHtml(device.name)}：${escapeHtml(device.status)}
          </span>
        `).join("")}
      </div>
    </section>
  `;
}

function renderHomeVisual(data, user) {
  const alertsByRoom = new Map(data.alerts.map((alert) => [alert.room_name, alert]));
  const canOperate = user.role !== "guest";

  return `
    <section class="panel home-demo" id="section-home-demo">
      <div class="panel-head">
        <div>
          <h2>全屋智能联动演示</h2>
          <p class="muted">实时设备态势与联动结果。</p>
        </div>
        <span class="tag info">可视化演示</span>
      </div>
      ${renderLivingRoomScene(data, canOperate, alertsByRoom)}
      <div class="house-stage" aria-label="全屋智能房屋态势图">
        ${data.rooms.map((room) => {
          const roomDevices = data.devices.filter((device) => device.room_name === room.name);
          const alert = alertsByRoom.get(room.name);
          const lightOn = roomDevices.some((device) => device.type === "light" && device.status === "on");
          const cameraOn = roomDevices.some((device) => device.type === "camera" && device.status !== "privacy" && device.online);
          const lockClosed = roomDevices.some((device) => device.type === "lock" && device.status === "locked");
          const sensorArmed = roomDevices.some((device) => device.type === "sensor" && device.status === "armed");
          const alarmActive = roomDevices.some((device) => device.type === "alarm" && device.status === "active");
          const roomState = alert || alarmActive ? "alert" : lightOn || cameraOn || sensorArmed ? "active" : "idle";

          return `
            <article class="room-tile ${roomVisualClass(room.name)} ${roomState}">
              <div class="room-topline">
                <strong>${escapeHtml(room.name)}</strong>
                ${alert ? `<span class="tag bad">告警</span>` : `<span class="tag ${roomState === "active" ? "ok" : "info"}">${roomState === "active" ? "运行中" : "待机"}</span>`}
              </div>
              <div class="room-scene">
                <span class="window ${cameraOn ? "online" : ""}"></span>
                <span class="lamp ${lightOn ? "on" : ""}"></span>
                <span class="sensor ${sensorArmed ? "armed" : ""} ${alert || alarmActive ? "warning" : ""}"></span>
                ${lockClosed ? `<span class="door-lock locked"></span>` : `<span class="door-lock"></span>`}
              </div>
              <p class="room-note">${escapeHtml(roomSummary(roomDevices, alert))}</p>
              <div class="room-devices">
                ${roomDevices.map((device) => `
                  <span class="mini-device ${isDeviceActive(device) ? "online" : ""}">
                    ${escapeHtml(device.name)}：${escapeHtml(device.status)}
                  </span>
                `).join("")}
              </div>
            </article>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

function renderCameras(devices) {
  const cameras = devices.filter((device) => device.type === "camera");
  return `
    <section class="panel">
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
    <section class="panel">
      <div class="panel-head">
        <h2>语音与场景</h2>
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

function renderAlerts(data, user) {
  const canOperate = user.role !== "guest";
  return `
    <section class="panel" id="section-alerts">
      <div class="panel-head">
        <h2>告警中心</h2>
        <span class="tag ${data.alerts.length ? "bad" : "ok"}">${data.alerts.length ? "需处理" : "正常"}</span>
      </div>
      ${canOperate ? `<form id="simulate-form" class="simulate-row">
        <label>房间
          <select name="room_id">
            ${data.rooms.map((room) => `<option value="${room.id}">${escapeHtml(room.name)}</option>`).join("")}
          </select>
        </label>
        <label>模拟事件
          <select name="event_type">
            <option value="intrusion">入侵</option>
            <option value="smoke">烟雾</option>
            <option value="fall">跌倒</option>
            <option value="door_open">门窗异常</option>
            <option value="motion">移动检测</option>
          </select>
        </label>
        <button class="danger" type="submit">触发模拟告警</button>
      </form>` : ""}
      <div class="list" style="margin-top: 14px;">
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
        <span class="tag info">事件索引</span>
      </div>
      <form id="recording-filter" class="filter-row">
        <label>关键词
          <input name="keyword" placeholder="烟雾、客厅、门窗" />
        </label>
        <button class="secondary" type="submit">检索</button>
      </form>
      <div class="list" id="recording-list" style="margin-top: 14px;">
        ${recordingItems(data.recordings)}
      </div>
    </section>
  `;
}

function recordingItems(recordings) {
  return recordings.map((recording) => `
    <article class="recording-item">
      <div class="device-title">
        <strong>${escapeHtml(recording.title)}</strong>
        <span class="tag info">${escapeHtml(recording.event_type)}</span>
      </div>
      <div class="muted">${escapeHtml(recording.room_name)} · ${escapeHtml(recording.started_at)} · ${recording.duration_seconds}s</div>
      <p>${escapeHtml(recording.summary)}</p>
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

function bindActions() {
  document.querySelectorAll("[data-section]").forEach((button) => {
    button.addEventListener("click", () => {
      const sectionId = button.dataset.section;
      const target = document.querySelector(`#section-${sectionId}`);
      if (!target) return;
      state.activeSection = sectionId;
      document.querySelectorAll("[data-section]").forEach((item) => {
        item.classList.toggle("active", item === button);
      });
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

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
      document.querySelector("#recording-list").innerHTML = recordingItems(payload.recordings);
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
