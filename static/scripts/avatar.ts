import "jquery"

$.when($.ready).done(() => {
  $("body").text("hello world!");
});
