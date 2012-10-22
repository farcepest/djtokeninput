$(document).ready(function(){
  $("input.tokeninput").each(function() {
    var field = $(this);

    field.tokenInput(
      field.data("search-url"),
      field.data("settings")
    );
  });
});
