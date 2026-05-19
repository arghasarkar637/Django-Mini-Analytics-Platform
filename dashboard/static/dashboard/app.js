const form = document.getElementById("uploadForm");
const fileType = document.getElementById("fileType");
const fileInput = document.getElementById("fileInput");
const messageBox = document.getElementById("messageBox");

const totalRows = document.getElementById("totalRows");
const successRows = document.getElementById("successRows");
const failedRows = document.getElementById("failedRows");
const errorList = document.getElementById("errorList");

const resultBox = document.getElementById("resultBox"); // optional if you still keep it in HTML

const menuItems = document.querySelectorAll(".menu-item");
const sections = document.querySelectorAll(".section");


// =========================
// MESSAGE
// =========================
function showMessage(msg, type = "info") {
    if (!messageBox) return;

    messageBox.style.display = "block";
    messageBox.textContent = msg;
    messageBox.className = "message-box " + type;
}


// =========================
// CSRF TOKEN
// =========================
function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");

        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();

            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }

    return cookieValue;
}

const csrftoken = getCookie("csrftoken");


// =========================
// RENDER RESULT
// =========================
function renderUploadResult(data) {
    if (totalRows) totalRows.textContent = data.total_rows ?? 0;
    if (successRows) successRows.textContent = data.inserted ?? 0;
    if (failedRows) failedRows.textContent = data.failed ?? 0;

    if (errorList) {
        if (data.errors && data.errors.length > 0) {
            errorList.innerHTML = data.errors.map(err => `
                <div class="error-item">
                    <strong>Row:</strong> ${JSON.stringify(err.row)}<br>
                    <strong>Error:</strong> ${err.error}
                </div>
            `).join("");
        } else {
            errorList.innerHTML = `<div class="success-note">No errors found.</div>`;
        }
    }

    if (resultBox) {
        resultBox.textContent = JSON.stringify(data, null, 2);
    }
}


// =========================
// FORM SUBMIT
// =========================
if (form) {
    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        const selectedType = fileType ? fileType.value : "csv";
        const file = fileInput ? fileInput.files[0] : null;

        if (!file) {
            showMessage("Please select a file first.", "error");
            return;
        }

        // CSV ONLY
        if (selectedType !== "csv") {
            showMessage("Currently only CSV upload is supported.", "error");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        try {
            showMessage("Uploading file...", "info");

            const response = await fetch("/api/v1/ingest/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken
                },
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                showMessage("Upload failed.", "error");
                renderUploadResult(data);
                return;
            }

            showMessage("Upload completed successfully.", "success");
            renderUploadResult(data);

        } catch (error) {
            showMessage("Something went wrong.", "error");

            if (resultBox) {
                resultBox.textContent = String(error);
            }

            if (errorList) {
                errorList.innerHTML = `<div class="error-item">${String(error)}</div>`;
            }
        }
    });
}


// =========================
// SIDEBAR NAVIGATION
// =========================
menuItems.forEach(item => {
    item.addEventListener("click", function () {
        // remove active
        menuItems.forEach(menu => {
            menu.classList.remove("active");
        });

        // add active
        this.classList.add("active");

        // hide all sections
        sections.forEach(section => {
            section.style.display = "none";
        });

        // show selected section
        const target = this.dataset.section;
        const targetSection = document.getElementById(target);

        if (targetSection) {
            targetSection.style.display = "block";
        }

        // topbar text update
        const topTitle = document.querySelector(".topbar h1");
        const topText = document.querySelector(".topbar p");

        if (topTitle && topText) {
            if (target === "dashboard-section") {
                topTitle.textContent = "Dashboard";
                topText.textContent = "Upload CSV files and validate analytics data.";
            } else if (target === "upload-section") {
                topTitle.textContent = "CSV Upload";
                topText.textContent = "Upload and validate your CSV files.";
            } else if (target === "analytics-section") {
                topTitle.textContent = "Analytics API";
                topText.textContent = "View analytics endpoint details.";
            }
        }
    });
});