(function($){
  $(document).ready(function(e){
    function toHide(e) {
      // Use a function since the div is added later
      return e.children('form, h3, div')
    }
    function createMsg(text, error) {
      var msg = $('<div class="system-message notice">').text(text)
      if (error) {
        msg.removeClass('notice').addClass('error')
      }
      return msg.hide()
    }
    var feed = $('#feedback-box'),
        toggler = $('#feedback-toggler')
    feed.css('display', 'block').data('showing', false)
    toHide(feed).hide()
    toggler.click(function() {
      if (feed.data('showing') == true) {
        feed.data('showing', false)
          .animate({
            width: 20, // see feedback.css
            height: 110, // see feedback.css
            paddingLeft: 0,
            paddingRight: 0,
            paddingTop: 0,
            paddingBottom: 0
          })
        $(this).attr('title', 'Show').animate({top: 5})
        toHide(feed).fadeOut('normal')
      } else {
        feed.data('showing', true)
          .animate({
            width: 300,
            height: 240,
            paddingLeft: 20,
            paddingRight: 10,
            paddingTop: 0,
            paddingBottom: 0
          })
        $(this).attr('title', 'Hide').animate({top: 135})
        toHide(feed).fadeIn('normal')
        $("#feedback-feedback").focus()
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
          var msg = createMsg(data.message)
          feed.append(msg)
          msg.fadeIn()
          setTimeout(function(){
            if (feed.data('showing'))
              toggler.trigger('click')
          }, 4000)
        },
        error: function() {
          var msg = createMsg('Failed to submit feedback!', true)
          $('h3', feed).after(msg.fadeIn('slow'))
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
        },
        error: function() {
          var msg = createMsg('Failed to delete feedback!', true)
          $('h1').after(msg.fadeIn('slow'))
       }
      })
      return false
    })
    /*
    // Make the box resizable
    // (Doesn't work, apparently resizable() changes the positioning from 
    // "right" to "left" so collapsing the box after it has been resized makes
    // it collapse from right to left instead of the other way around)
    feed.resizable({handles: 'n,s,w',
                    // Change textarea width on resize
                    resize: function(evt, ui) {
                      // This is weird (new ta width should be feed width - padding imho)
                      $('#feedback-feedback').width(feed.width())
                    }
    })
    */ 
  })
})(jQuery)
