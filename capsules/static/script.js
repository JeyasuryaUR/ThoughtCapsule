function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getSummary(text, csrftoken) {
    return fetch('/summarize/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ text: text })
    })
    .then(response => {
        
        return response.json();
    })
    .then(data => {
        if(data.error) {
            console.error(data.error);
        } else {
            return data.summary
        }
    });
}

function updateTagSuggestions(csrftoken) {
    var text = document.getElementById('capsule-content').value;
    var currentTags = document.getElementById('capsule-tags').value.split(',').map(tag => tag.trim());

    fetch('/generate-tags/', {
        method: 'POST',
        body: JSON.stringify({text: text, current_tags: currentTags}),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        }
    })
    .then(response => response.json())
    .then(data => {
        var tagContainer = document.getElementById('tag-suggestions');
        tagContainer.innerHTML = '';
        if (data.tags.length === 0) {
            var messageElement = document.createElement('span');
            messageElement.textContent = 'Start typing or type further for suggestions';
            tagContainer.appendChild(messageElement);
        } else {
            data.tags.forEach(function(tag) {
                var tagElement = document.createElement('span');
                tagElement.textContent = tag;
                tagElement.style.cursor = 'pointer';
                tagElement.style.padding = '5px';
                tagElement.style.border = '1px solid #ccc';
                tagElement.style.marginRight = '5px';
                tagElement.addEventListener('click', function() {
                    var capsuleTags = document.getElementById('capsule-tags');
                    if (capsuleTags.value.trim() !== '' && capsuleTags.value.trim().slice(-1) !== ',') {
                        capsuleTags.value += ', ';
                    }
                    capsuleTags.value += tag + ', ';
                    updateTagSuggestions(csrftoken);
                });
                tagContainer.appendChild(tagElement);
            });
        }
    });
}

function startDictation(inpId) {
    if (window.hasOwnProperty('webkitSpeechRecognition')) {
        var recognition = new webkitSpeechRecognition();

        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.lang = "en-US";
        recognition.start();

        recognition.onresult = function(e) {
            document.getElementById(inpId).value = e.results[0][0].transcript;
            recognition.stop();
        };

        recognition.onerror = function(e) {
            console.error(e);
            recognition.stop();
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    var csrftoken = getCookie('csrftoken');

    var fab = document.createElement('a');
    fab.setAttribute('href', "create/");
    fab.setAttribute('class', 'fab-btn btn btn-primary');
    fab.innerHTML = '<i class="fas fa-plus"></i><span class="fab-label">New Capsule</span>';

    document.body.appendChild(fab);

    function updateCountAndSummary(text) {
        document.getElementById('accept-summary').style.display = 'none';
        document.getElementById('summary-group').style.display = 'block';
        document.getElementById('capsule-summary').value = "Summarizing...";
        var wordCount = text.split(' ').filter(word => word !== '').length; 
        var wordCounter = document.getElementById('word-counter');
        wordCounter.textContent = wordCount + '/100';
        if (wordCount > 100) {
            wordCounter.classList.remove('text-muted');
            wordCounter.classList.add('text-danger');

            getSummary(text, csrftoken).then(summary => {
                document.getElementById('capsule-summary').value = summary;
                document.getElementById('accept-summary').style.display = 'block';
            });

        } else {
            wordCounter.classList.remove('text-danger');
            wordCounter.classList.add('text-muted');

            document.getElementById('summary-group').style.display = 'none';
        }
    }

    var debounceTimer;
    document.getElementById('capsule-content').addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function() {
            updateTagSuggestions(csrftoken);
            updateCountAndSummary(document.getElementById('capsule-content').value.trim());
        }, 500);
    });

    document.getElementById('capsule-tags').addEventListener('input', function() {
        updateTagSuggestions(csrftoken);
    });

    document.getElementById('accept-summary').addEventListener('click', function() {
        var summary = document.getElementById('capsule-summary').value.trim();
        document.getElementById('capsule-content').value = summary;
        updateCountAndSummary(summary);
    });


});