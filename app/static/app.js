const form = document.getElementById("upload-form");
const input = document.getElementById("file-input");
const pick = document.getElementById("pick");
const dropHint = document.getElementById("drop-hint");
const fileName = document.getElementById("file-name");
const submit = document.getElementById("submit");
const progress = document.getElementById("progress");
const result = document.getElementById("result");
const shareUrl = document.getElementById("share-url");
const copyBtn = document.getElementById("copy");
const openLink = document.getElementById("open-link");
const metaLine = document.getElementById("meta-line");
const errorEl = document.getElementById("error");

function setFile(file) {
  if (!file) return;
  fileName.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} МБ)`;
  submit.disabled = false;
  errorEl.hidden = true;
}

pick.addEventListener("click", () => input.click());
input.addEventListener("change", () => setFile(input.files[0]));

["dragenter", "dragover"].forEach((ev) =>
  form.addEventListener(ev, (e) => { e.preventDefault(); form.classList.add("drag"); })
);
["dragleave", "drop"].forEach((ev) =>
  form.addEventListener(ev, (e) => { e.preventDefault(); form.classList.remove("drag"); })
);
form.addEventListener("drop", (e) => {
  const f = e.dataTransfer.files[0];
  if (f) { input.files = e.dataTransfer.files; setFile(f); }
});

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const file = input.files[0];
  if (!file) return;

  const data = new FormData();
  data.append("file", file);

  submit.disabled = true;
  progress.hidden = false;
  progress.value = 0;
  errorEl.hidden = true;

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/upload");
  xhr.upload.onprogress = (ev) => {
    if (ev.lengthComputable) progress.value = (ev.loaded / ev.total) * 100;
  };
  xhr.onload = () => {
    submit.disabled = false;
    progress.hidden = true;
    if (xhr.status !== 200) {
      let msg = "Ошибка загрузки";
      try { msg = JSON.parse(xhr.responseText).detail || msg; } catch {}
      errorEl.textContent = msg;
      errorEl.hidden = false;
      return;
    }
    const res = JSON.parse(xhr.responseText);
    const absolute = new URL(res.url, window.location.origin).href;
    shareUrl.value = absolute;
    openLink.href = res.url;
    metaLine.textContent = `${res.original_name} · до ${new Date(res.expires_at).toLocaleString()}`;
    result.hidden = false;
  };
  xhr.onerror = () => {
    submit.disabled = false;
    progress.hidden = true;
    errorEl.textContent = "Сетевая ошибка";
    errorEl.hidden = false;
  };
  xhr.send(data);
});

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(shareUrl.value);
    copyBtn.textContent = "Скопировано";
    setTimeout(() => (copyBtn.textContent = "Копировать"), 1500);
  } catch {
    shareUrl.select();
    document.execCommand("copy");
  }
});