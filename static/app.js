const searchForm = document.querySelector("#searchForm");
const nameInput = document.querySelector("#universityName");
const countrySelect = document.querySelector("#countrySelect");
const resultMessage = document.querySelector("#resultMessage");
const resultsTitle = document.querySelector("#resultsTitle");
const resultsGrid = document.querySelector("#universityResults");
const statusMessage = document.querySelector("#statusMessage");
const exportActions = document.querySelector("#exportActions");
const compareButton = document.querySelector("#compareButton");
const comparisonResults = document.querySelector("#comparisonResults");

let lastSearch = null;

function setStatus(message = "", isError = false) {
    statusMessage.textContent = message;
    statusMessage.hidden = !message;
    statusMessage.classList.toggle("is-error", isError);
}

function addTextElement(parent, tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    element.textContent = text;
    parent.append(element);
    return element;
}

function safeWebsite(value) {
    if (typeof value !== "string") return "";
    try {
        const url = new URL(value.startsWith("http") ? value : `https://${value}`);
        return ["https:", "http:"].includes(url.protocol) ? url.href : "";
    } catch {
        return "";
    }
}

function renderUniversity(university) {
    const card = document.createElement("article");
    card.className = "university-card";
    const top = document.createElement("div");
    top.className = "university-card-top";
    addTextElement(top, "span", "uni-monogram", (university.name || "U").slice(0, 1).toUpperCase());
    addTextElement(top, "span", "uni-country", university.country || "International");
    card.append(top);
    addTextElement(card, "h4", "uni-name", university.name || "University");

    const domains = Array.isArray(university.domains) ? university.domains : [];
    if (domains.length) addTextElement(card, "p", "uni-domain", domains[0]);

    const websites = Array.isArray(university.web_pages) ? university.web_pages : [];
    const website = websites.map(safeWebsite).find(Boolean);
    const link = document.createElement("a");
    link.className = "uni-link";
    if (website) {
        link.href = website;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = "Visit website ↗";
    } else {
        link.textContent = "Website unavailable";
        link.setAttribute("aria-disabled", "true");
    }
    card.append(link);
    return card;
}

async function loadUniversities(name, country) {
    lastSearch = { name, country };
    resultsGrid.replaceChildren();
    exportActions.hidden = true;
    setStatus("Looking across the world…");
    resultsTitle.textContent = "Finding your possibilities";

    const params = new URLSearchParams();
    if (name) params.set("name", name);
    if (country) params.set("country", country);

    try {
        const response = await fetch(`/api/search?${params}`);
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.message || "We couldn't load universities right now.");

        const universities = data.universities || [];
        resultsTitle.textContent = `${data.total.toLocaleString()} ${data.total === 1 ? "university" : "universities"} to explore`;
        resultMessage.textContent = country ? `Live results in ${country}${name ? ` matching “${name}”` : ""}.` : `Live results matching “${name}”.`;
        if (!universities.length) {
            setStatus("No universities matched that search. Try another name or country.");
        } else {
            setStatus("");
            universities.slice(0, 15).forEach((university) => resultsGrid.append(renderUniversity(university)));
            if (universities.length > 15) {
                addTextElement(resultsGrid, "p", "results-note", `Showing 15 of ${data.total.toLocaleString()} results. Download CSV or JSON for the complete list.`);
            }
            exportActions.hidden = false;
        }
    } catch (error) {
        resultsTitle.textContent = "We'll try again in a moment.";
        resultMessage.textContent = "The live university directory is temporarily unavailable.";
        setStatus(error.message, true);
    }
}

searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const name = nameInput.value.trim();
    const country = countrySelect.value;
    if (!name && !country) {
        setStatus("Enter a university name or choose a country to search.", true);
        nameInput.focus();
        return;
    }
    loadUniversities(name, country);
});

exportActions.addEventListener("click", (event) => {
    const button = event.target.closest("[data-export]");
    if (!button || !lastSearch) return;
    const params = new URLSearchParams({ type: button.dataset.export });
    if (lastSearch.name) params.set("name", lastSearch.name);
    if (lastSearch.country) params.set("country", lastSearch.country);
    window.location.assign(`/api/export?${params}`);
});

compareButton.addEventListener("click", async () => {
    const countries = [...document.querySelectorAll(".compare-country")]
        .map((select) => select.value)
        .filter(Boolean);
    comparisonResults.replaceChildren();
    if (countries.length < 2) {
        addTextElement(comparisonResults, "p", "comparison-message is-error", "Choose at least two countries to compare.");
        return;
    }
    if (new Set(countries).size !== countries.length) {
        addTextElement(comparisonResults, "p", "comparison-message is-error", "Choose a different country in each selected row.");
        return;
    }

    compareButton.disabled = true;
    compareButton.textContent = "Comparing live data…";
    try {
        const response = await fetch("/api/compare", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ countries }),
        });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.message || "We couldn't compare those countries.");
        const maximum = Math.max(1, ...data.results.map((item) => item.total));
        data.results.forEach((item) => {
            const row = document.createElement("div");
            row.className = "comparison-row";
            const title = document.createElement("div");
            title.className = "comparison-row-title";
            addTextElement(title, "strong", "", item.country);
            addTextElement(title, "span", "", `${item.total.toLocaleString()} universities`);
            row.append(title);
            const track = document.createElement("div");
            track.className = "comparison-track";
            const bar = document.createElement("span");
            bar.style.width = `${Math.max(3, (item.total / maximum) * 100)}%`;
            track.append(bar);
            row.append(track);
            comparisonResults.append(row);
        });
    } catch (error) {
        addTextElement(comparisonResults, "p", "comparison-message is-error", error.message);
    } finally {
        compareButton.disabled = false;
        compareButton.innerHTML = 'Compare countries <span aria-hidden="true">↗</span>';
    }
});
