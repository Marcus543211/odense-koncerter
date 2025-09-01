const searchForm = document.getElementById("search");
searchForm.addEventListener("submit", search);

const concerts2 = document.getElementsByClassName("concert");

function search(event) {
  event.preventDefault();
  const text = event.target[0].value.toLowerCase();
  for (const concert of concerts2) {
    const title = concert.getAttribute("data-title");
    const hasText = title.includes(text);
    concert.hidden = !hasText;
  }
}
