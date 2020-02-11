function uploadHandwrittenPages() {
    console.log("AHOJ");
    var form = document.getElementById("BMOD_upload_form");
    if (form.files.length == 0) {
        console.log("NO FILE");
        document.getElementById("BMOD_upload_form_no_file_message").style.visibility = "visible";
    } else {
        console.log("OK");
        form.submit();
    }
}