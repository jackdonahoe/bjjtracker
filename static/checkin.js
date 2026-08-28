const nameInput = document.getElementById("name-input");
const personIdInput = document.getElementById("person-id");
const suggestionsList = document.getElementById("suggestions");

let debounceTimer;

nameInput.addEventListener("input", () => {
    personIdInput.value = "";
    clearTimeout(debounceTimer);

    const q = nameInput.value.trim();
    if (!q) {
        suggestionsList.innerHTML = "";
        return;
    }

    debounceTimer = setTimeout(() => search(q), 200);
});

async function search(q) {
    const response = await fetch(`/api/people/search?q=${encodeURIComponent(q)}`);
    const people = await response.json();
    renderSuggestions(people);
}

function renderSuggestions(people) {
    suggestionsList.innerHTML = "";
    for (const person of people) {
        const li = document.createElement("li");
        li.textContent = person.full_name;
        li.addEventListener("click", () => selectPerson(person));
        suggestionsList.appendChild(li);
    }
}

function selectPerson(person) {
    nameInput.value = person.full_name;
    personIdInput.value = person.id;
    suggestionsList.innerHTML = "";
}
