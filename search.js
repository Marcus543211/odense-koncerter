const searchField = document.getElementById("search");
searchField.addEventListener("input", search);

const concerts2 = document.getElementsByClassName("concert");

function search(event) {
  const text = searchField.value.toLowerCase();
  for (const concert of concerts2) {
    const title = concert.getAttribute("data-title");
    const isMatch = title.includes(text);
    concert.hidden = !isMatch;
  }
}
