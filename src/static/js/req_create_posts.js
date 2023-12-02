$(document).ready(function(){
    $("#create").click(function(){
         var site = $('#site').val();
         var links = []

         const checkbox = document.getElementById('allPostsCheckbox');
         var postsNum = 0

         var showModal = true;

         if (!checkbox.checked){
             postsNum = $('#inputPostsNum').val();
             if (postsNum < 0){
                showModal = false;
                alert('Počet článkov nemôže byť nižší ako 0.');
                return;
             }
         }
         
         $('.article-link').each(function() {
             links.push($(this).val());
         });

         console.log("Site:", site);
         console.log("Links:", links);
         console.log("Number:", postsNum);
         
         fetch(`/get_posts_data?site=${site}&links=${links}&number=${postsNum}`, {
             method: "GET"
         })
         .then(response => response.json())
         .then(postsData => {
             data_posts = JSON.stringify(postsData);
             return fetch(`/get_stories_template?site=${site}`, {
                 method: "GET"
             });
         })
         .then(response => response.json())
         .then(templateData => {
             template = JSON.stringify(templateData);
             console.log("POSTS:", data_posts);
             console.log("TEMPLATE:", template);
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
         .then(response => response.json())
         .then(result => {
             window.location.href = `/show_images?site=${site}`;
         })
         if(showModal){
            $('#loadingModal').modal('show');
         }

    });
});