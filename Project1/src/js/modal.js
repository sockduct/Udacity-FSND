// Get reference to the modal and relevant image
var modal = document.getElementById('descrModal');
var img = document.getElementById('fpeModal');

// When the user clicks on the image, open the modal
img.onclick = function() {
    modal.style.display = "block";
}

// Get reference to the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
    modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

