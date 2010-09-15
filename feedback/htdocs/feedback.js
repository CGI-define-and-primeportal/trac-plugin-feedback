(function($){
  $(document).ready(function(e){
    function toHide(e) {
      // Use a function since the div is added later
      return e.children('form, h3, div')
    }
    var feed = $('#feedback-box'),
        toggler = $('#feedback-toggler'),
    feed.css('display', 'block').data('showing', false)
        .css('bottom', $('#footer').height()) // Might calculate a better position later
    toHide(feed).hide()
    toggler.click(function() {
      if (feed.data('showing') == true) {
        feed.data('showing', false)
          .animate({
            width: 25,
            height: 110,
            padding: 0
          })
        toHide(feed).fadeOut('normal')
        $(this).attr('title', 'Show').animate({top: 5})
      } else {
        feed.data('showing', true)
          .animate({
            width: 300,
            height: 200,
            padding: '0 10px 0 20px'
          })
        toHide(feed).fadeIn('normal')
        $(this).attr('title', 'Hide').animate({top: 85})
      }
    })
    var form = feed.children('form')
    form.submit(function() {
      $.ajax({
        url: form.attr('action'),
        type: 'POST',
        data: form.serializeArray(),
        dataType: 'json',
        success: function(data) {
          form.fadeOut().empty()
          var msg = $('<div class="system-message notice">').text(data.message).hide()
          feed.append(msg)
          msg.fadeIn()
          setTimeout(function(){
            if (feed.data('showing')) 
              toggler.trigger('click')
          }, 4000)
        }
      })
      return false
    })
    $('#feedback-list a.delete').click(function(){
      if (!confirm('Do you really want to delete this feedback item?'))
        return false
      var link = $(this)
      $.ajax({
        url: link.attr('href'), // Item id is in the url
        data: $('#token-form').serializeArray(), // We need the form token
        type: 'POST',
        dataType: 'json',
        success: function (data) {
          link.parent('li').fadeOut('slow')
        }
      })
      return false
    })
  })
})(jQuery)
