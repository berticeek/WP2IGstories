$(document).ready(function () {
    $("#download_stories").click(function() {
        window.location.href = `/download_stories?site=${site}`;
    });

    $("#sendMail").click(function() {
        var emailInput = document.getElementById('input-mail');
        mail = emailInput.value;

        var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (emailRegex.test(mail)) {
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
            });
        }
        else {
            alert('Zadaj správnu mailovú adresu');
        }
    });
});