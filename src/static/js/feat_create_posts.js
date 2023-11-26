function addInput() {
    var container = document.getElementById('links-articles');
    var count = container.children.length; - 1

    var input = document.createElement('input');
    input.type = 'text';
    input.className = 'article-link';
    input.id = 'article-link' + count;
    input.name = 'article-link' + count;
    container.appendChild(input);
}

function checkIfAllPosts() {
    const checkbox = document.getElementById('allPostsCheckbox');
    const inputPostsNumber = document.getElementById('postsNumber');

    checkbox.addEventListener('change', function() {
        if (!checkbox.checked) {
            inputPostsNumber.style.display = "flex";
        } else {
            inputPostsNumber.style.display = "none";
        }
    });
}

document.addEventListener('DOMContentLoaded', checkIfAllPosts);