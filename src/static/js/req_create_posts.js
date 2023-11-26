$(document).ready(function(){
    $("#create").click(function(){
         var site = $('#site').val();
         var links = []

         const checkbox = document.getElementById('allPostsCheckbox');
         var postsNum = 0
         if (!checkbox.checked){
             postsNum = $('#inputPostsNum').val();
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
         .then(response => response.json())
         .then(postsElementsList => {
             posts_elements = postsElementsList;
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


    });
});