/* QT 影音庫 — 動態渲染、書卷篩選、搜尋（含 debounce）、播放燈箱 */
(function () {
  "use strict";
  var root = document.querySelector(".qtlib");
  if (!root) return;

  var srcUrl = root.getAttribute("data-qtlib-src") || "/data/qtvideos.json";
  var bookBtns = Array.prototype.slice.call(root.querySelectorAll(".qtlib__book"));
  var currentEl = root.querySelector("[data-qtlib-current]");
  var searchEl = root.querySelector("[data-qtlib-search]");
  var gridEl = root.querySelector("[data-qtlib-grid]");
  var emptyEl = root.querySelector("[data-qtlib-empty]");
  var moreWrap = root.querySelector("[data-qtlib-more-wrap]");
  var moreBtn = root.querySelector("[data-qtlib-more]");
  var modal = document.querySelector("[data-qtlib-modal]");
  var player = document.querySelector("[data-qtlib-player]");
  var modalTitle = document.querySelector("[data-qtlib-modal-title]");

  var BATCH = 60;
  var data = null;
  var state = { testament: "", book: "", q: "", limit: BATCH };

  function esc(s) {
    return String(s || "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function norm(s) {
    return String(s || "").toLowerCase().replace(/\s+/g, "");
  }

  function cardHtml(v) {
    var title = esc(v.passage);
    var date = esc(v.date);
    var yt = encodeURIComponent(v.yt || "");
    return (
      '<article class="qtlib__card">' +
        '<button type="button" class="qtlib__thumb" data-yt="' + yt + '" data-title="' + title + '" aria-label="播放 ' + title + '">' +
          '<img loading="lazy" width="320" height="180" src="https://i.ytimg.com/vi/' + yt + '/mqdefault.jpg" alt="' + title + '">' +
          '<span class="qtlib__play" aria-hidden="true">▶</span>' +
        "</button>" +
        '<div class="qtlib__info">' +
          '<span class="qtlib__cardtitle">' + title + "</span>" +
          '<span class="qtlib__carddate">' + date + "</span>" +
        "</div>" +
      "</article>"
    );
  }

  function render() {
    if (!data || !gridEl) return;
    var q = norm(state.q);
    var groups = [];
    var totalMatched = 0;

    (data.testaments || []).forEach(function (t) {
      if (state.testament && t.id !== state.testament) return;
      (t.books || []).forEach(function (b) {
        if (state.book && b.name !== state.book) return;
        var vids = (b.videos || []).filter(function (v) {
          if (!q) return true;
          return norm((v.passage || "") + " " + (v.date || "") + " " + b.name).indexOf(q) !== -1;
        });
        if (!vids.length) return;
        totalMatched += vids.length;
        groups.push({ testament: t.name, book: b.name, videos: vids });
      });
    });

    if (!totalMatched) {
      gridEl.innerHTML = "";
      if (emptyEl) emptyEl.hidden = false;
      if (moreWrap) moreWrap.hidden = true;
      return;
    }

    if (emptyEl) emptyEl.hidden = true;

    // 選單一書卷時全部列出；「全部影片」或搜尋時分批渲染避免一次塞上千個 DOM
    var cap = state.book ? Infinity : state.limit;
    var remaining = cap;
    var html = [];

    for (var i = 0; i < groups.length && remaining > 0; i++) {
      var g = groups[i];
      var slice = remaining === Infinity ? g.videos : g.videos.slice(0, remaining);
      remaining = remaining === Infinity ? Infinity : remaining - slice.length;
      html.push(
        '<section class="qtlib__section">' +
          '<h3 class="qtlib__section-hd">' + esc(g.testament) + " · " + esc(g.book) +
            "<small>" + g.videos.length + " 支</small></h3>" +
          '<div class="qtlib__cards">' + slice.map(cardHtml).join("") + "</div>" +
        "</section>"
      );
    }

    gridEl.innerHTML = html.join("");

    var shown = Math.min(totalMatched, cap);
    if (moreWrap && moreBtn) {
      if (shown < totalMatched) {
        moreBtn.textContent = "載入更多影片（已顯示 " + shown + " / " + totalMatched + " 支）";
        moreWrap.hidden = false;
      } else {
        moreWrap.hidden = true;
      }
    }
  }

  bookBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      bookBtns.forEach(function (b) { b.classList.remove("is-active"); });
      btn.classList.add("is-active");
      state.testament = btn.getAttribute("data-testament") || "";
      state.book = btn.getAttribute("data-book") || "";
      state.limit = BATCH;
      if (currentEl) currentEl.textContent = btn.getAttribute("data-name") || "全部影片";
      render();
    });
  });

  if (searchEl) {
    var timer = 0;
    searchEl.addEventListener("input", function () {
      window.clearTimeout(timer);
      timer = window.setTimeout(function () {
        state.q = searchEl.value;
        state.limit = BATCH;
        render();
      }, 150);
    });
  }

  if (moreBtn) {
    moreBtn.addEventListener("click", function () {
      state.limit += BATCH;
      render();
    });
  }

  function openModal(yt, title) {
    if (!modal || !player || !yt) return;
    player.innerHTML =
      '<iframe src="https://www.youtube.com/embed/' +
      encodeURIComponent(yt) +
      '?autoplay=1&rel=0" title="' +
      esc(title) +
      '" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen loading="lazy"></iframe>';
    if (modalTitle) modalTitle.textContent = title || "";
    modal.hidden = false;
    document.documentElement.style.overflow = "hidden";
  }

  function closeModal() {
    if (!modal || modal.hidden) return;
    modal.hidden = true;
    if (player) player.innerHTML = "";
    document.documentElement.style.overflow = "";
  }

  // 掛在 document：燈箱在 .qtlib 容器外，掛在 root 會收不到燈箱內的點擊
  document.addEventListener("click", function (e) {
    var thumb = e.target.closest && e.target.closest(".qtlib__thumb");
    if (thumb) {
      e.preventDefault();
      openModal(thumb.getAttribute("data-yt"), thumb.getAttribute("data-title"));
      return;
    }
    if (e.target.closest && e.target.closest("[data-qtlib-close]")) closeModal();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeModal();
  });

  fetch(srcUrl, { credentials: "same-origin" })
    .then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(function (json) {
      data = json;
      render();
    })
    .catch(function () {
      if (gridEl) gridEl.innerHTML = '<div class="qtlib__empty">影片清單載入失敗，請重新整理。</div>';
    });
})();
