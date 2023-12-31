$(document).ready(function(){
    $("#create").click(function(){

        // First reset modal
        document.getElementById('loading_modal_progress').style.display = "block";
        document.getElementById('loading_modal_failed').style.display = "none";
        document.getElementById('loadingModalHead').style.display = "none";

         var site = $('#site').val();
         var links = []

         const checkbox = document.getElementById('allPostsCheckbox');
         var postsNum = 0

         var showModal = true;

        $('.article-link').each(function() {
            const linkValue = $(this).val().trim();
            if (linkValue !== ''){
                links.push($(this).val());
            }
        });

        // Select date
        var postsFrom = document.getElementById("postsFromDate").value;

         if (!checkbox.checked){
            console.log("Length: ", links.length);
             postsNum = $('#inputPostsNum').val();
             if (postsNum < 0){
                showModal = false;
                alert('Počet článkov nemôže byť nižší ako 0.');
                return;
             }
             if ((postsNum === "" || postsNum === 0) && links.length === 0){
                showModal = false;
                alert('Zadaj odkazy na články, alebo počet článkov, ktoré chceš vygenerovať');
                return;
             }
         }

         console.log("Site:", site);
         console.log("Links:", links);
         console.log("Number:", postsNum);
         console.log("Date:", postsFrom);
         
         fetch(`/get_posts_data?site=${site}&links=${links}&number=${postsNum}&from_date=${postsFrom}`, {
             method: "GET"
         })
         .then(response => {
            if (!response.ok){
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
         .then(postsData => {
            if (postsData.success){
                data_posts = JSON.stringify(postsData.data);
            } else{
                console.error(`Server error: ${postsData.error}`);
            }
             return fetch(`/get_stories_template?site=${site}`, {
                 method: "GET"
             });
         })
         .then(response => {
            if (!response.ok){
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        }) 
        .then(templateData => {
            if (templateData.success){
                template = JSON.stringify(templateData.data);
            } else {
                console.error(`Server error: ${templateData.error}`);
            }
             return fetch(`/get_posts_elements?posts=${data_posts}&template=${template}`, {
                 method: "GET"
             });
         })
         .then(response => {
            if (!response.ok){
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();

         })
         .then(postsElementsList => {
            if (postsElementsList.success) {
                posts_elements = postsElementsList.data;
            } else {
                console.error(`Server error: ${postsElementsList.error}`);
            }
             
             return fetch(`/create_images`, {
                 method: "POST",
                 headers: {
                     'Content-Type': 'application/json',
                 },
                 body: JSON.stringify({
                     site: site,
                     posts_elements: posts_elements,
                 }),
             });
         })
         .then(response => {
            if (!response.ok){
                // Hide loading circle and display info about error to user
                document.getElementById('loading_modal_progress').style.display = "none";
                document.getElementById('loading_modal_failed').style.display = "block";
                document.getElementById('loadingModalHead').style.display = "block";
                throw new Error(`HTTP error! Status: ${response.status}`);
            } else {
                return response.json()
            }
         })
         .then(result => {
             window.location.href = `/show_images?site=${site}`;
         })
         .catch(error => {
            console.error('Error:', error.message);
         });
         
        // Display loading modal if no alert was raised
         if(showModal){
            $('#loadingModal').modal('show');
         }

    });
});