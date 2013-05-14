(function($){
  $(document).ready(function(e){
    function createMsg(text, error) {
      var msg = $('<div class="system-message notice">').text(text)
      if (error) {
        msg.removeClass('notice').addClass('error')
      }
      return msg.hide()
    }
    var feed = $('#feedback-dialog'),
        toggler = $('#feedback-trigger'),
        form = $('#feedback-form')
    toggler.click(function(){
      feed.dialog({modal:true, title: 'Feedback', width:500, height:360})
      form.show()
      feed.find('.system-message').remove()
    })
    form.submit(function() {
      $.ajax({
        url: form.attr('action'),
        type: 'POST',
        data: form.serializeArray(),
        dataType: 'json',
        success: function(data) {
          form.fadeOut()
          $('#feedback-feedback').val('')
          var msg = createMsg(data.message)
          feed.append(msg)
          msg.fadeIn()
          setTimeout(function(){
            feed.dialog('close')
          }, 3000)
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
  })
})(jQuery)
