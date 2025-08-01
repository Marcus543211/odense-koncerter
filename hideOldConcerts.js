// This script hides the old concerts. It must be included with defer.

// Find the time at midnight today since some concerts lack more precision.
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
