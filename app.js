document.addEventListener("DOMContentLoaded", function () {
    // Timer logic
    let timerElement = document.getElementById("timer");
    if (timerElement) {
        let timeLeft = 60; // 60 seconds per question
        timerElement.textContent = `Time left: ${timeLeft}s`;

        let countdown = setInterval(function () {
            timeLeft--;
            timerElement.textContent = `Time left: ${timeLeft}s`;

            if (timeLeft <= 0) {
                clearInterval(countdown);
                // Auto-submit form when time is up
                document.getElementById("quizForm").submit();
            }
        }, 1000);
    }

    // Prevent submit without selecting an option
    let form = document.getElementById("quizForm");
    if (form) {
        form.addEventListener("submit", function (event) {
            let options = document.querySelectorAll("input[name='answer']");
            let checked = false;
            options.forEach((opt) => {
                if (opt.checked) checked = true;
            });

            if (!checked) {
                event.preventDefault();
                alert("Please select an option before submitting!");
            }
        });
    }
});
