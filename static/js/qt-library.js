/* QT 影音庫 — 書卷篩選、搜尋、播放燈箱 */
(function () {
  "use strict";
  var root = document.querySelector(".qtlib");
  if (!root) return;

  var bookBtns = Array.prototype.slice.call(root.querySelectorAll(".qtlib__book"));
  var sections = Array.prototype.slice.call(root.querySelectorAll(".qtlib__section"));
  var currentEl = root.querySelector("[data-qtlib-current]");
  var searchEl = root.querySelector("[data-qtlib-search]");
  var emptyEl = root.querySelector("[data-qtlib-empty]");
  var modal = document.querySelector("[data-qtlib-modal]");
  var player = document.querySelector("[data-qtlib-player]");
  var modalTitle = document.querySelector("[data-qtlib-modal-title]");

  var state = { testament: "", book: "", q: "" };

  function norm(s) {
    return (s || "").toLowerCase().replace(/\s+/g, "");
  }

  function apply() {
    var q = norm(state.q);
    var shown = 0;
    sections.forEach(function (sec) {
      var active = state.book
        ? sec.getAttribute("data-testament") === state.testament &&
          sec.getAttribute("data-book") === state.book
        : true;
      if (!active) {
        sec.hidden = true;
        return;
      }
      var any = false;
      Array.prototype.forEach.call(sec.querySelectorAll(".qtlib__card"), function (card) {
        var ok = !q || norm(card.getAttribute("data-text")).indexOf(q) !== -1;
        card.hidden = !ok;
        if (ok) {
          any = true;
          shown++;
        }
      });
      sec.hidden = !any;
    });
    if (emptyEl) emptyEl.hidden = shown !== 0;
  }

  bookBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      bookBtns.forEach(function (b) {
        b.classList.remove("is-active");
      });
      btn.classList.add("is-active");
      state.testament = btn.getAttribute("data-testament") || "";
      state.book = btn.getAttribute("data-book") || "";
      if (currentEl) currentEl.textContent = btn.getAttribute("data-name") || "全部影片";
      apply();
    });
  });

  if (searchEl) {
    searchEl.addEventListener("input", function () {
      state.q = searchEl.value;
      apply();
    });
  }

  function openModal(yt, title) {
    if (!modal || !player || !yt) return;
    player.innerHTML =
      '<iframe src="https://www.youtube.com/embed/' +
      encodeURIComponent(yt) +
      '?autoplay=1&rel=0" title="' +
      (title || "").replace(/"/g, "&quot;") +
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

  apply();
})();
