$(document).ready(function () {
   $("input[type='file']").change(function () {
       if (this.files[0].name.endsWith(".prj")) {
           $("#load-project").submit();
       } else {
           alert("Wrong file type");
       }
   });

   $("input[type='file']").hover(function () {
       $(this).parent().children("span").css("font-size", "16px").css("font-weight", "bold");
   }, function () {
       $(this).parent().children("span").css("font-size", "15px").css("font-weight", "normal");
   });
});