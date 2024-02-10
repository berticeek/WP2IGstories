$(document).ready(function () {
    $("#download_stories").click(function() {
        window.location.href = `/download_stories?site=${site}`;
    });

    $("#sendMail").click(function() {
        var emailInput = document.getElementById('input-mail');
        mail = emailInput.value;

        var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (emailRegex.test(mail)) {

            // Hide mail form, display loading bar
            document.getElementById("mail-pre-send").style.display = "none";
            document.getElementById("sendMail").style.display = "none";
            document.getElementById("mail-sending").style.display = "block";

            const svg = document.getElementById('progress_loader')
            svg.classList.add('progress-loader')

            var links = [];
            $('.story').each(function () {
                links.push($(this).data('url'));
            });

            fetch(`/send_by_email`, {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    site: site,
                    links: links,
                    mail: mail,
                }),
            })
            .then(response => {
                if (!response.ok){
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(mailStatus => {
                // Change loading circle to check or fail
                if (mailStatus.success) {
                    console.log("Done!")
                    svg.classList.remove('progress-loader');
                    svg.classList.add('ready-loader');
                } else {
                    console.log(`Sending e-mail failed ${mailStatus.error}`)
                    document.getElementById("mail-sending").style.display = "none";
                    // svg.style.display = "none"
                    document.getElementById("mail-sent-fail").style.display = "block";
                }
            })
        }
        else {
            alert('Zadaj správnu mailovú adresu');
        }
    });

    // Reset content of modal with email form to initial state
    $("#send_mail_button ").click(function() {
        document.getElementById("mail-pre-send").style.display = "block";
        document.getElementById("sendMail").style.display = "block";
        document.getElementById("mail-sending").style.display = "none";
    });

    // Show value of the slider for background position
    var sliders = document.getElementsByClassName("bg-pos-slider");
    var outputs = document.getElementsByClassName("bg-pos-value");

    for (var i=0; i<sliders.length; i++){
        outputs[i].value = sliders[i].value;

        sliders[i].addEventListener('input', function() {
            var index = Array.prototype.indexOf.call(sliders, this);
            outputs[index].value = this.value;
        });

        outputs[i].addEventListener('input', function() {
            var index = Array.prototype.indexOf.call(outputs, this);
            sliders[index].value = this.value;
        });
    }
});

function deleteStory(story_number){
    fetch(`/delete_story/${site}/${story_number}`, {method: 'DELETE'})
        .then(response => {
            if (!response.ok){
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(result => {
            if (result.success) {
                window.location.href = `/show_images?site=${site}`;
            } else {
                console.log(`Removing story failed ${result.error}`)
            }
        })
}