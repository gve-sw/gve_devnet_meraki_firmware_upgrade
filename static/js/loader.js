
/*Loading indicator on button*/
function showLoadingText() {
    document.getElementById("login-submit").value = "Loading ...";
}

function showOriginalText(originalButtonText){
    document.getElementById("login-submit").value = originalButtonText;
}

function importButton() {
    document.getElementById("upload_link").innerHTML = "Loading from CSV...";
}

function submitButton() {
    document.getElementById("submit_link").innerHTML = "Scheduling upgrades...";
}

                          
  