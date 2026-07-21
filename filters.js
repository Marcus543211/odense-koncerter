// This function drives the filters.
//
// It is wrapped in a function to avoid scoping issues.

(function () {
  const concerts = document.getElementsByClassName("concert");

  const quizFilter = document.getElementById("hide-quizzes");
  quizFilter.addEventListener("input", filterAll);
  const jamFilter = document.getElementById("hide-jams");
  jamFilter.addEventListener("input", filterAll);
  const jazzFestFilter = document.getElementById("hide-jazz-fest");
  jazzFestFilter.addEventListener("input", filterAll);
  const nashvilleFilter = document.getElementById("hide-nashville");
  nashvilleFilter.addEventListener("input", filterAll);

  const searchField = document.getElementById("search");
  searchField.addEventListener("input", filterAll);

  function filterAll(event) {
    showAll();
    hideByQuizFilter();
    hideByJamFilter();
    hideByJazzFestFilter();
    hideByNashvilleFilter();
    hideBySearch();
  }

  function showAll() {
    for (const concert of concerts) {
      concert.hidden = false;
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
      const isNashville = title.includes("nashville nights 2026");
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

  const jamRegexes = [
    /jazz jam.*/,
    /dexter jam.*/,
    /blue monday blues jam/,
    /jamsession v\..* \/\/ odense jazz festival/,
    /jam night.*nashville nights 2026/,
  ];

  const jazzFestConcerts = new Set([
    "m. o. n. g. // odense jazz festival",
    "fini sings with strings",
    "britta virves trio // odense jazz festival",
    "carl winther trio feat. randy brecker",
    "anna pauline group feat. randy brecker, janis siegel, john di martino // odense jazz festival",
    "masterclass v. janis siegel // odense jazz festival",
    "viktoria søndergaard music of secrets",
    "jakob dinesen – slow flow // odense jazz festival",
    "jamsession v. simon krebs // odense jazz festival",
    "elements  of  refusal",
    "jamsession v. chano olskær // odense jazz festival",
    "kresten osgood quintet 100 år med dansk jazz // odense jazz festival",
    "tribute to thilo",
    "buki yamaz // odense jazz festival",
    "jamsession v. søren høst // odense jazz festival",
    "øjne & ører: ki!",
    "giacomo smith ? joe webb ? snorre kirk ? anders fjelds",
    "odense jazz orchestra plays dąbrowski // odense jazz festival",
  ]);
})();

