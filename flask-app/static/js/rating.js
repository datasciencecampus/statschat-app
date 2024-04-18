function recordRating(rating_text, color) {
    // Send an AJAX request to record the rating value
    if (color == "font-size:16px;color:red;")
        {rating = 0} else {rating = 1};
    $.ajax({
        url: '/record_rating',
        type: 'POST',
        data: {rating: rating, comment: rating_text},
        success: function(response) {
            console.log('Rating recorded successfully');
        },
        error: function(xhr, status, error) {
            console.log('Error recording rating: ' + error);
        }
    });
}

$('#thumbs-up-ico').click(function(){
    $('#thumbs-up-ico').attr("style", "font-size:24px;color:green;");
    $('#thumbs-down-ico').attr("style", "font-size:24px;color:grey;");
    $('#feedback-send-input').attr("style", "font-size:16px;");
    $('#feedback-send-icon').attr("style", "font-size:16px;color:green;");
});

$('#thumbs-down-ico').click(function(){
    $('#thumbs-up-ico').attr("style", "font-size:24px;color:grey;");
    $('#thumbs-down-ico').attr("style", "font-size:24px;color:red;");
    $('#feedback-send-input').attr("style", "font-size:16px;");
    $('#feedback-send-icon').attr("style", "font-size:16px;color:red;");
});

$('#feedback-send-icon').click(function(){
    recordRating($('#feedback-send-input').val(), $('#feedback-send-icon').attr("style"));
    $('#thumbs-up-ico').attr("style", "display:none;");
    $('#thumbs-down-ico').attr("style", "display:none;");
    $('#feedback-send-input').attr("style", "display:none;");
    $('#feedback-send-icon').text(" Thank you.");
});
