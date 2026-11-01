const state = { presets: {} };
const elements = {
  refreshHealth: document.querySelector("#refreshHealth"),
  health: document.querySelector("#health"),
  speechForm: document.querySelector("#speechForm"),
  speechAudio: document.querySelector("#speechAudio"),
  speechResult: document.querySelector("#speechResult"),
  presetForm: document.querySelector("#presetForm"),
  presetList: document.querySelector("#presetList"),
  singForm: document.querySelector("#singForm"),
  singAudio: document.querySelector("#singAudio"),
  singResult: document.querySelector("#singResult"),
  refreshLogs: document.querySelector("#refreshLogs"),
  logs: document.querySelector("#logs"),
};

function formData(form) {
  const value = {};
  for (const field of new FormData(form)) value[field[0]] = field[1];
  return value;
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  const text = await response.text();
  let value;
  try { value = JSON.parse(text); } catch { value = { raw: text }; }
  if (!response.ok) throw new Error(value.message || value.error || `HTTP ${response.status}`);
  return value;
}

async function loadHealth() {
  try {
    const data = await request("/api/health");
    elements.health.replaceChildren();
    for (const [key, value] of Object.entries(data)) {
      const label = document.createElement("span");
      label.textContent = key;
      const content = document.createElement("span");
      content.textContent = value ?? "-";
      elements.health.append(label, content);
    }
  } catch (error) { elements.health.textContent = error.message; }
}

async function loadPresets() {
  try {
    const data = await request("/api/presets");
    state.presets = data.presets || {};
    renderPresets();
  } catch (error) { elements.presetList.textContent = error.message; }
}

function renderPresets() {
  const names = Object.keys(state.presets);
  if (!names.length) { elements.presetList.textContent = "暂无预设"; return; }
  elements.presetList.innerHTML = "";
  for (const name of names) {
    const preset = state.presets[name];
    const item = document.createElement("div");
    item.className = "preset";
    const presetName = document.createElement("div");
    presetName.className = "name";
    presetName.textContent = name;
    const description = document.createElement("div");
    description.className = "desc";
    description.textContent = preset.control_instruction || "";
    item.append(presetName, description);
    const useButton = document.createElement("button");
    useButton.textContent = "选用";
    useButton.onclick = () => applyPreset(preset);
    const deleteButton = document.createElement("button");
    deleteButton.textContent = "删除";
    deleteButton.onclick = async () => {
      if (!confirm(`删除预设「${name}」？`)) return;
      await request("/api/presets/delete", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name }) });
      await loadPresets();
    };
    item.append(useButton, deleteButton);
    elements.presetList.append(item);
  }
}

function applyPreset(preset) {
  const form = elements.speechForm;
  if (preset.target_f0) form.target_f0.value = preset.target_f0;
  if (preset.tempo) form.tempo.value = preset.tempo;
  if (preset.cfg_value) form.cfg_value.value = preset.cfg_value;
  if (preset.inference_timesteps) form.inference_timesteps.value = preset.inference_timesteps;
  if (preset.control_instruction) form.control_instruction.value = preset.control_instruction;
  if (preset.reference_audio_path) form.reference_audio_path.value = preset.reference_audio_path;
  syncLabels();
}

async function submitSpeech(event) {
  event.preventDefault();
  const value = formData(elements.speechForm);
  const payload = {
    text: value.text,
    control_instruction: value.control_instruction,
    reference_audio_path: value.reference_audio_path || null,
    target_f0: Number(value.target_f0),
    tempo: Number(value.tempo),
    cfg_value: Number(value.cfg_value),
    inference_timesteps: Number(value.inference_timesteps),
    output_format: value.output_format,
    normalize_loudness: true,
  };
  elements.speechResult.textContent = "合成中…";
  try {
    const result = await request("/api/speak", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    elements.speechAudio.src = result.url;
    elements.speechResult.textContent = JSON.stringify(result, null, 2);
  } catch (error) { elements.speechResult.textContent = error.message; }
}

async function submitPreset(event) {
  event.preventDefault();
  const speech = formData(elements.speechForm);
  const value = formData(elements.presetForm);
  const payload = {
    name: value.name,
    overwrite: Boolean(value.overwrite),
    target_f0: Number(speech.target_f0),
    tempo: Number(speech.tempo),
    cfg_value: Number(speech.cfg_value),
    inference_timesteps: Number(speech.inference_timesteps),
    control_instruction: speech.control_instruction,
    reference_audio_path: speech.reference_audio_path || null,
  };
  try {
    await request("/api/presets/save", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    await loadPresets();
  } catch (error) { alert(error.message); }
}

async function submitSing(event) {
  event.preventDefault();
  const value = formData(elements.singForm);
  const payload = {
    target_metadata_path: value.target_metadata_path,
    prompt_wav_path: value.prompt_wav_path || null,
    prompt_metadata_path: value.prompt_metadata_path || null,
    device: value.device,
    control: value.control,
    pitch_shift: Number(value.pitch_shift || 0),
    auto_shift: Boolean(value.auto_shift),
    output_format: "mp3",
    normalize_loudness: true,
  };
  elements.singResult.textContent = "合成中…";
  try {
    const result = await request("/api/sing", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    elements.singAudio.src = result.url;
    elements.singResult.textContent = JSON.stringify(result, null, 2);
  } catch (error) { elements.singResult.textContent = error.message; }
}

async function loadLogs() {
  try {
    const result = await request("/api/logs");
    elements.logs.textContent = result.lines.join("\n") || "暂无日志";
  } catch (error) { elements.logs.textContent = error.message; }
}

function syncLabels() {
  const pairs = [["target_f0", value => `${value} Hz`], ["tempo", value => `${Number(value).toFixed(2)}x`], ["cfg_value", value => Number(value).toFixed(1)], ["inference_timesteps", value => value]];
  for (const [name, format] of pairs) {
    const input = elements.speechForm[name];
    const output = input.nextElementSibling;
    if (output) output.textContent = format(input.value);
  }
}

elements.refreshHealth.onclick = loadHealth;
elements.refreshLogs.onclick = loadLogs;
elements.speechForm.onsubmit = submitSpeech;
elements.presetForm.onsubmit = submitPreset;
elements.singForm.onsubmit = submitSing;
for (const input of elements.speechForm.querySelectorAll("input[type=range]")) input.oninput = syncLabels;
syncLabels();
loadHealth();
loadPresets();
loadLogs();
