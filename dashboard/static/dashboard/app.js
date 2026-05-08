const form = document.getElementById("uploadForm");
const fileType = document.getElementById("fileType");
const fileInput = document.getElementById("fileInput");
const resultBox = document.getElementById("resultBox");
const messageBox = document.getElementById("messageBox");


// =========================
// MESSAGE
// =========================

function showMessage(msg, type = "info") {

    messageBox.style.display = "block";

    messageBox.textContent = msg;

    messageBox.className = "message-box " + type;
}


// =========================
// CSRF TOKEN
// =========================

function getCookie(name) {

    let cookieValue = null;

    if (document.cookie && document.cookie !== '') {

        const cookies = document.cookie.split(';');

        for (let i = 0; i < cookies.length; i++) {

            const cookie = cookies[i].trim();

            if (cookie.substring(0, name.length + 1) === (name + '=')) {

                cookieValue = decodeURIComponent(
                    cookie.substring(name.length + 1)
                );

                break;
            }
        }
    }

    return cookieValue;
}

const csrftoken = getCookie('csrftoken');


// =========================
// FORM SUBMIT
// =========================

form.addEventListener("submit", async function (e) {

    e.preventDefault();

    const selectedType = fileType.value;

    const file = fileInput.files[0];

    if (!file) {

        showMessage(
            "Please select a file first.",
            "error"
        );

        return;
    }


    // CSV ONLY

    if (selectedType !== "csv") {

        showMessage(
            "Currently only CSV upload is supported.",
            "error"
        );

        return;
    }


    const formData = new FormData();

    formData.append("file", file);


    try {

        showMessage(
            "Uploading file...",
            "info"
        );

        const response = await fetch(
            "/api/v1/ingest/",
            {
                method: "POST",

                headers: {
                    "X-CSRFToken": csrftoken
                },

                body: formData
            }
        );

        const data = await response.json();


        if (!response.ok) {

            showMessage(
                "Upload failed.",
                "error"
            );

            resultBox.textContent = JSON.stringify(
                data,
                null,
                2
            );

            return;
        }


        showMessage(
            "Upload completed successfully.",
            "success"
        );

        resultBox.textContent = JSON.stringify(
            data,
            null,
            2
        );

    }

    catch (error) {

        showMessage(
            "Something went wrong.",
            "error"
        );

        resultBox.textContent = String(error);
    }

});


const menuItems = document.querySelectorAll(".menu-item");

const sections = document.querySelectorAll(".section");


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

        const targetSection =
            document.getElementById(target);

        if (targetSection) {
            targetSection.style.display = "block";
        }

    });

});