$(document).ready(function () {
    $('#recreate').click(function () {

        // First reset modal
        document.getElementById('loading_modal_progress').style.display = "block";
        document.getElementById('loading_modal_failed').style.display = "none";
        document.getElementById('loadingModalHead').style.display = "none";

        var storiesData = [];
        console.log("site: ", site)

        // Iterate through each .story div
        $('.story').each(function () {
            var min_position_x = $(this).find('input[name="position_slider"]').attr('min');
            var center_position_x = $(this).find('input[name="position_value"]').val();
            console.log("Min pos: ", min_position_x);
            console.log("Center pos: ", center_position_x);
            var storyData = {
                'image_position_x': (min_position_x - center_position_x).toString(),
                'texts': []
            };

            // Iterate through each textarea within the current .story div
            $(this).find('textarea[name="text"]').each(function () {
                storyData['texts'].push($(this).val());
            });

            // Include other parameters from the original story
            $.extend(storyData, {
                'number': $(this).data('number'), // Replace with the actual data attribute name
                'url': $(this).data('url'),
                'image': $(this).data('image'),
            });

            storiesData.push(storyData);
        });

        fetch(`/recreate_posts_metadata`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                data_stories: storiesData
            }),
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
            } else {
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
                posts_elements = JSON.stringify(postsElementsList.data);
            } else {
                console.error(`Server error: ${postsElementsList.error}`);
            }
            return fetch(`/adjust_posts_elements?elements=${posts_elements}&metadata=${JSON.stringify(storiesData)}`, {
                method: "GET"
            });
        })
        .then(response => {
            if(!response.ok){
                document.getElementById('loading_modal_progress').style.display = "none";
                document.getElementById('loading_modal_failed').style.display = "block";
                document.getElementById('loadingModalHead').style.display = "block";
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(adjustedPostsElementsList => {
            if (adjustedPostsElementsList.success) {
                adjusted_posts_elements = adjustedPostsElementsList.data;
            } else {
                console.error(`Server error: ${adjustedPostsElementsList.error}`)
            }
            return fetch(`/create_images`, {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    site: site,
                    posts_elements: adjusted_posts_elements,
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
    });
});