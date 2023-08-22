function recordRating(rating) {
    // Send an AJAX request to record the rating value
    $.ajax({
        url: '/record_rating',
        type: 'POST',
        data: { rating: rating },
        success: function(response) {
            console.log('Rating recorded successfully');
        },
        error: function(xhr, status, error) {
            console.log('Error recording rating: ' + error);
        }
    });
}


$('#star_0').click(function(){
    $('#star_0').attr("src", "../../static/rating/rating_fill.png");
    $('#star_1').attr("src", "../../static/rating/rating.png");
    $('#star_2').attr("src", "../../static/rating/rating.png");
    $('#star_3').attr("src", "../../static/rating/rating.png");
    $('#star_4').attr("src", "../../static/rating/rating.png");
    $('#ratings').attr("src","../../static/rating/x_unhappy.png");
    recordRating(1);
});
$('#star_1').click(function(){
    $('#star_0').attr("src", "../../static/rating/rating_fill.png");
    $('#star_1').attr("src", "../../static/rating/rating_fill.png");
    $('#star_2').attr("src", "../../static/rating/rating.png");
    $('#star_3').attr("src", "../../static/rating/rating.png");
    $('#star_4').attr("src", "../../static/rating/rating.png");
    $('#ratings').attr("src","../../static/rating/unhappy.png");
    recordRating(2);
});
$('#star_2').click(function(){
    $('#star_0').attr("src", "../../static/rating/rating_fill.png");
    $('#star_1').attr("src", "../../static/rating/rating_fill.png");
    $('#star_2').attr("src", "../../static/rating/rating_fill.png");
    $('#star_3').attr("src", "../../static/rating/rating.png");
    $('#star_4').attr("src", "../../static/rating/rating.png");
    $('#ratings').attr("src","../../static/rating/ok.png");
    $('#rating_content').attr('value','3');
    recordRating(3);
});
$('#star_3').click(function(){
    $('#star_0').attr("src", "../../static/rating/rating_fill.png");
    $('#star_1').attr("src", "../../static/rating/rating_fill.png");
    $('#star_2').attr("src", "../../static/rating/rating_fill.png");
    $('#star_3').attr("src", "../../static/rating/rating_fill.png");
    $('#star_4').attr("src", "../../static/rating/rating.png");
    $('#ratings').attr("src","../../static/rating/happy.png");
    recordRating(4);
});
$('#star_4').click(function(){
    $('#star_0').attr("src", "../../static/rating/rating_fill.png");
    $('#star_1').attr("src", "../../static/rating/rating_fill.png");
    $('#star_2').attr("src", "../../static/rating/rating_fill.png");
    $('#star_3').attr("src", "../../static/rating/rating_fill.png");
    $('#star_4').attr("src", "../../static/rating/rating_fill.png");
    $('#ratings').attr("src","../../static/rating/xtrahappy.png");
    recordRating(5);
});
