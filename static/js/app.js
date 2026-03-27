// Add basic confirm prompts for delete actions.
document.addEventListener("DOMContentLoaded", function () {
    const forms = document.querySelectorAll(".delete-form");
    forms.forEach((form) => {
        form.addEventListener("submit", function (event) {
            const ok = window.confirm("Are you sure you want to delete this item?");
            if (!ok) {
                event.preventDefault();
            }
        });
    });
});
