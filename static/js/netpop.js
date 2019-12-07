
// Testing Functions (interactive.html test)

$(function() {
    $('a#process_input').bind('click', function() {
    $.getJSON('/background_process', {
        proglang: $('input[name="proglang"]').val(),
    }, function(data) {
        $("#result").text(data.result);
    });
    return false;
    });
});


// drag-n-drop for multi endpoint import
var dragHandler = function(evt){
    evt.preventDefault();
};

var dropHandler = function(evt){
    evt.preventDefault();
    var files = evt.originalEvent.dataTransfer.files;
    console.log(files[0]);
};

var dropHandlerSet = {
    dragover: dragHandler,
    drop: dropHandler
};

$(".droparea").on(dropHandlerSet);