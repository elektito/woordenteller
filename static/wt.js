function remove_word(word, elem) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/remove?word=' + word);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onload = function(e) {
        var msgbox = document.querySelector('#msgbox');
        if (xhr.status == 200) {
            msgbox.innerHTML = `'${word}' removed from database.`;
            msgbox.classList.add('success-msg');
        } else {
            msgbox.innerHTML = `Could not remove '${word}' from database.`;
            msgbox.classList.add('error-msg');
        }

        response = e.target.response;
        word_count_label = document.querySelector('#wordcount')
        if (word_count_label) {
            word_count_label.textContent = response['nwords'];
        }

        // remove the word box from the page
        console.log(elem.parentNode);
        elem.parentNode.removeChild(elem);
    };
    xhr.responseType = 'json';
    xhr.send();
}
