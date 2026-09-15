// This function drives the filters.
//
// It is wrapped in a function to avoid scoping issues.

(function () {
  const concerts = document.getElementsByClassName("concert");

  const quizFilter = document.getElementById("hide-quizzes");
  quizFilter.addEventListener("input", filterAll);
  const jamFilter = document.getElementById("hide-jams");
  jamFilter.addEventListener("input", filterAll);
  const soldOutFilter = document.getElementById("hide-sold-out");
  soldOutFilter.addEventListener("input", filterAll);
  //const jazzFestFilter = document.getElementById("hide-jazz-fest");
  //jazzFestFilter.addEventListener("input", filterAll);
  //const nashvilleFilter = document.getElementById("hide-nashville");
  //nashvilleFilter.addEventListener("input", filterAll);

  const searchField = document.getElementById("search");
  searchField.addEventListener("input", filterAll);

  function filterAll(event) {
    showAll();
    hideOldConcerts();
    hideByQuizFilter();
    hideByJamFilter();
    hideBySoldOutFilter();
    //hideByJazzFestFilter();
    //hideByNashvilleFilter();
    hideBySearch();
  }

  const jamRegexes = [
    /jazz jam.*/,
    /dexter jam.*/,
    /blue monday blues jam/,
    /jamsession v\..* \/\/ odense jazz festival/,
    /jam night.*nashville nights 2026/,
  ];

  const jazzFestConcerts = new Set([
  ]);

  function showAll() {
    for (const concert of concerts) {
      concert.hidden = false;
    }
  }

  function hideOldConcerts() {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    const concerts = document.querySelectorAll(".concert");
    for (const concert of concerts) {
      const time = concert.querySelector("time");
      const concertDate = new Date(time.dateTime);
      if (concertDate < today) {
        concert.hidden = true;
      }
    }
  }

  function hideByQuizFilter() {
    const isActivated = quizFilter.checked;
    if (!isActivated) return;

    for (const concert of concerts) {
      const title = concert.getAttribute("data-title");
      // I hope no band name includes "quiz"...
      const isQuiz = title.includes("quiz");
      concert.hidden = concert.hidden || isQuiz;
    }
  }

  function hideByJamFilter() {
    const isActivated = jamFilter.checked;
    if (!isActivated) return;

    for (const concert of concerts) {
      const title = concert.getAttribute("data-title");
      const isJam = jamRegexes.some((r) => r.test(title));
      concert.hidden = concert.hidden || isJam;
    }
  }

  function hideBySoldOutFilter() {
    const isActivated = soldOutFilter.checked;
    if (!isActivated) return;

    for (const concert of concerts) {
      const isSoldOut = concert.hasAttribute("data-is-sold-out");
      concert.hidden = concert.hidden || isSoldOut;
    }
  }

  function hideByJazzFestFilter() {
    const isActivated = jazzFestFilter.checked;
    if (!isActivated) return;

    for (const concert of concerts) {
      const title = concert.getAttribute("data-title");
      const isJazzFest = jazzFestConcerts.has(title);
      concert.hidden = concert.hidden || isJazzFest;
    }
  }

  function hideByNashvilleFilter() {
    const isActivated = nashvilleFilter.checked;
    if (!isActivated) return;

    for (const concert of concerts) {
      const title = concert.getAttribute("data-title");
      const isNashville = title.includes("nashville nights");
      concert.hidden = concert.hidden || isNashville;
    }
  }

  function hideBySearch() {
    const text = searchField.value.toLowerCase();

    for (const concert of concerts) {
      const title = concert.getAttribute("data-title");
      const isMatch = title.includes(text);
      concert.hidden = concert.hidden || !isMatch;
    }
  }

  // Run the filters to hide old concerts.
  filterAll(null);
})();

