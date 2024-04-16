$(document).ready(function(){
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/answer');

    //receive message details from server
    socket.on('newanswer', function(msg) {
        $('#answer_block').html(msg.answer);
    });

});
