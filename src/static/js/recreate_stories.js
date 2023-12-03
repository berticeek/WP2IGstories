$(document).ready(function () {
    $('#recreate').click(function () {
        var storiesData = [];
        console.log("site: ", site)

        // Iterate through each .story div
        $('.story').each(function () {
            var storyData = {
                'image_position_x': $(this).find('input[name="position"]').val(),
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
        .then(response => response.json())
        .then(postsData => {
            data_posts = JSON.stringify(postsData);
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
        .then(response => response.json())
        .then(adjustedPostsElementsList => {
            adjusted_posts_elements = adjustedPostsElementsList;
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