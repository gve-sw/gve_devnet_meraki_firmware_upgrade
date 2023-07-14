$(function() {
    /*Show corresponding network list as soon as organization is choosen in dropdown + reset child fields*/
    $('#organizations_select').bind('change', function() {
          $('.network-select').attr("hidden", true);
          $('.network-select .networks').val("0");
          $('.network-select .networks').attr("required", true);
          $('.camera-checkboxes').attr("hidden", true);
          var selectid = $( "#organizations_select option:selected" ).val();
          $('#' + selectid).attr("hidden",false);       
      });                            
  });  

  $(function(){
    $("#upload_link").on('click', function(e){
        e.preventDefault();
        $("#upload:hidden").trigger('click');
        document.getElementById("upload").value=""
    });

    $('#upload').on('change', function (e){
        let file = document.getElementById("upload").files[0];
    
        console.log("Uploading file...");
        const API_ENDPOINT = "/extract-networks";
        const request = new XMLHttpRequest();
        const formData = new FormData();

        request.open("POST", API_ENDPOINT, true);
        
        request.onreadystatechange = () => {
        if (request.readyState === XMLHttpRequest.DONE && request.status === 200) {
            console.log(request.responseText);
            window.location.href='./'
        }
        };
        formData.append("file", file);

        request.send(formData);
        document.getElementById("upload").value=""
    } );
});

function selectVersion(e) {
    console.log(e)
    var device = e.value.split('.')[0]
    boxes = document.getElementsByName("checkbox-version-" + device);
    if (e.checked) {
        for (let i = 0; i < boxes.length; i++) {
            if (boxes[i] !== e) {
                boxes[i].disabled = true;
            }
        }
    } else {
        for (let i = 0; i < boxes.length; i++) {
            if (boxes[i] !== e) {
                boxes[i].disabled = false;
            }
        }
    }
}

function selectOutdated() {
    var checkboxes = document.getElementsByName('network');
    for (let i = 0; i < checkboxes.length; i++) {
        console.log(checkboxes[i].parentElement.parentElement.parentElement.style.backgroundColor)
        if (checkboxes[i].parentElement.parentElement.parentElement.getAttribute('name') == "outdated") {
            checkboxes[i].checked = true;
        }
    }
}