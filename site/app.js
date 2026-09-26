(() => {
  const data = window.TIYA_DATA;
  const state = { query: "", language: "全部", style: "全部", shown: 36, queueStatus: "queued" };
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => [...document.querySelectorAll(selector)];
  const normalize = (value) => String(value || "").toLocaleLowerCase().replace(/[\s·'’“”"，,。.！!？?（）()\-—_]/g, "");

  const languages = ["全部", ...new Set(data.songs.map(song => song.language))];
  const preferredStyles = ["热门必点", "元气", "治愈", "炸场", "伤感", "摇滚", "古风", "民谣", "说唱", "电音", "暗黑", "复古", "影视", "二游/电子", "二游", "K-POP", "J-POP", "歌手专属", "经典", "流行"];
  const available = new Set(data.songs.map(song => song.style));
  const styles = ["全部", ...preferredStyles.filter(style => available.has(style))];

  function makePill(label, type, active) {
    const button = document.createElement("button");
    button.className = `pill${active ? " active" : ""}`;
    button.textContent = label;
    button.dataset[type] = label;
    return button;
  }

  languages.forEach(language => $("#language-filters").appendChild(makePill(language, "language", language === state.language)));
  styles.forEach(style => $("#style-filters").appendChild(makePill(style, "style", style === state.style)));

  function matches(song) {
    const term = normalize(state.query);
    const haystack = normalize([song.title, song.artist, song.style, song.language].join(" "));
    return (!term || haystack.includes(term)) &&
      (state.language === "全部" || song.language === state.language) &&
      (state.style === "全部" || song.style === state.style);
  }

  function songMeta(song) {
    return [song.artist, song.style, song.language].filter(Boolean).join(" · ");
  }

  async function copySong(song) {
    const text = `我要点《${song.title}》`;
    try {
      await navigator.clipboard.writeText(text);
    } catch (_) {
      const area = document.createElement("textarea");
      area.value = text; document.body.appendChild(area); area.select(); document.execCommand("copy"); area.remove();
    }
    showToast(`已复制：${text}`);
  }

  function songCard(song) {
    const article = document.createElement("article");
    article.className = "song-card";
    article.innerHTML = `<span class="note" aria-hidden="true">♪</span><div class="song-info"><strong></strong><span></span></div><button class="copy-btn" aria-label="复制点歌">⧉</button>`;
    article.querySelector("strong").textContent = song.title;
    article.querySelector(".song-info span").textContent = songMeta(song);
    article.querySelector(".copy-btn").addEventListener("click", () => copySong(song));
    article.addEventListener("dblclick", () => copySong(song));
    return article;
  }

  function renderSongs() {
    const filtered = data.songs.filter(matches);
    const list = $("#song-list");
    list.replaceChildren(...filtered.slice(0, state.shown).map(songCard));
    $("#result-count").textContent = filtered.length;
    $("#empty-state").hidden = filtered.length !== 0;
    $("#load-more").hidden = filtered.length <= state.shown;
    $("#reset-filters").hidden = !state.query && state.language === "全部" && state.style === "全部";
  }

  function setFilter(type, value) {
    state[type] = value; state.shown = 36;
    $$(`[data-${type}]`).forEach(button => button.classList.toggle("active", button.dataset[type] === value));
    renderSongs();
  }

  $("#language-filters").addEventListener("click", event => event.target.dataset.language && setFilter("language", event.target.dataset.language));
  $("#style-filters").addEventListener("click", event => event.target.dataset.style && setFilter("style", event.target.dataset.style));
  $("#search").addEventListener("input", event => { state.query = event.target.value; state.shown = 36; $("#clear-search").hidden = !state.query; renderSongs(); });
  $("#clear-search").addEventListener("click", () => { $("#search").value = ""; state.query = ""; $("#clear-search").hidden = true; renderSongs(); $("#search").focus(); });
  $("#reset-filters").addEventListener("click", () => { $("#search").value = ""; state.query = ""; $("#clear-search").hidden = true; setFilter("language", "全部"); setFilter("style", "全部"); });
  $("#load-more").addEventListener("click", () => { state.shown += 36; renderSongs(); });
  $("#random-song").addEventListener("click", () => {
    const candidates = data.songs.filter(matches);
    if (!candidates.length) return showToast("当前筛选下没有歌曲");
    copySong(candidates[Math.floor(Math.random() * candidates.length)]);
  });

  function renderQueue() {
    const items = data.queue[state.queueStatus];
    $("#queue-list").replaceChildren(...items.map((item, index) => {
      const article = document.createElement("article");
      article.className = "queue-item";
      const learned = state.queueStatus === "learned";
      article.innerHTML = `<span class="queue-num"></span><div class="queue-song"><strong></strong><span></span></div><span class="status-badge${learned ? " done" : ""}">${learned ? "已学会" : "排队中"}</span>`;
      article.querySelector(".queue-num").textContent = learned ? "✓" : String(index + 1).padStart(2, "0");
      article.querySelector("strong").textContent = item.title;
      article.querySelector(".queue-song span").textContent = item.requester ? `点歌人：${item.requester}` : "学习计划";
      return article;
    }));
  }

  $$(".queue-tab").forEach(button => button.addEventListener("click", () => {
    state.queueStatus = button.dataset.status;
    $$(".queue-tab").forEach(tab => tab.classList.toggle("active", tab === button));
    renderQueue();
  }));

  $$(".nav-btn").forEach(button => button.addEventListener("click", () => {
    const songs = button.dataset.view === "songs";
    $("#songs-view").hidden = !songs; $("#queue-view").hidden = songs;
    $$(".view").forEach(view => view.classList.toggle("active", !view.hidden));
    $$(".nav-btn").forEach(nav => nav.classList.toggle("active", nav === button));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }));

  let toastTimer;
  function showToast(message) {
    const toast = $("#toast"); toast.textContent = message; toast.classList.add("show");
    clearTimeout(toastTimer); toastTimer = setTimeout(() => toast.classList.remove("show"), 1900);
  }

  $("#queued-count").textContent = data.queue.queued.length;
  $("#learned-count").textContent = data.queue.learned.length;
  $("#updated-date").textContent = data.updated;
  renderSongs(); renderQueue();
})();
