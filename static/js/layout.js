////first, checks if it isn't implemented yet
//if (!String.prototype.format) {
  //String.prototype.format = function() {
    //var args = arguments;
    //return this.replace(/{(\d+)}/g, function(match, number) { 
      //return typeof args[number] != 'undefined'
        //? args[number]
        //: match
      //;
    //});
  //};
//}

//$(function() {
    //var resizebody = function() {
        //$('body').css(
            //'width',
            //'{0}px'.format($('html').width() - 2 * $('#nav').width())
        //);
    //};
    //resizebody();
    //$(window).bind('resize', resizebody);
//});

$(function() {
    var url = location.href.substr(0, location.href.length - location.hash.length);
    $('#nav a').each(function() {
        if (this.href == url) {
            $(this).addClass('current');
        }
    });
});

//$(function() {
    //var toc = $('.toc');
    //$('.content').find('h1, h2, h3, h4').each(function(i, e) {
        //$('<' + e.tagName + '/>').text($(e).text()).appendTo(toc);
    //});
//});
