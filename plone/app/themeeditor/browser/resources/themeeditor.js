$(function() {
  var updateResults = function() {
    $('#plone-app-themeeditor-tags .selected').removeClass('selected');
    $('#plone-app-themeeditor-browser').load(
      '@@plone.app.themeeditor.browse #plone-app-themeeditor-browser', 
      $('#plone-app-themeeditor-filter-form').serialize()
    );
  }
  var activateUI = function() {
    // edit popups
    $('a[href*="/@@plone.app.themeeditor.export"]', this).prepOverlay({
      subtype: 'ajax',
      filter: '#content',
      //formselector: 'form',
          });


    $('a[href*="/manage_main"],a[href*="/@@customizezpt"]', this).prepOverlay({
      subtype: 'ajax',
      filter: 'form,form+*', // everything after the 2nd table
      formselector: 'form',
      afterpost: function(el){
        el.find('input[name=submit]').attr('name', 'x-browser');
      },
      config: {
        onLoad: function() {
          // absolutize relative form actions
          var base = this.getTrigger().data('pbo').src
          $('form', this.getOverlay()).each(function() {
            // jquerytools.form does not accept input elements those name is submit
            // zope never checks that anyway
            $(this).find('input[name=submit]').attr('name', 'x-browser');
            var action = $(this).attr('action');
            if (action.charAt(0) != '/') {
              $(this).attr('action', base.substr(0,base.lastIndexOf('/')) + '/' + action);
            }
          });
          
          // prevent customizing already-customized resources
          var source = this.getTrigger().data('pbo').source
          if(source.find('.plone-app-themeeditor-layers.customized').size() >= 1){
              var overlay = this.getOverlay();
              overlay.find('input[type=submit]').hide();
              overlay.find('select[name=folder_path]').parent().parent().remove();
          }
        },
        onClose: function(){
          var trigger = this.getTrigger().data('pbo').source.parent();
          var title = trigger.prev('.plone-app-themeeditor-resource.open');
          trigger.load(title.attr('href'), null, function(){
            // remove custom and view info
            var dd = title.next();
            while (dd.is('dd')) {
                var to_remove = dd; dd = dd.next(); to_remove.remove();
            }
            var dd = $(this).find('dd');
            title.after(dd);
            dd.show();
            activateUI.apply(dd);
          });
        }
      }
    });
    // removal of customized items
    $('a[href*="/manage_delObjects"]', this).click(function(e) {
      e.preventDefault();
      jq.get($(this).attr('href'));
      $(this).closest('dd').remove();
    });
  }
  activateUI.apply($('#plone-app-themeeditor-export'));
  activateUI.apply($('#plone-app-themeeditor-browser'));
  // update results via AJAX
  $('#plone-app-themeeditor-filter-form').submit(function(e) {
    e.preventDefault();
    updateResults();
  });
  // collapsible layer lists
  $('a.plone-app-themeeditor-resource-link').live('click', function(e) {
    e.preventDefault();
    var link = $(this);
    link.toggleClass('open');
    var dd = $(this).next();
    if (dd.is('dd')) {
      while(dd.is('dd')) { dd.slideToggle('fast'); dd = dd.next(); }
    } else {
      $('<div><' + '/div>').load($(this).attr('href'), null, function() {
        $('dd', this).insertAfter(link).slideDown('fast').each(function() {
          activateUI.apply(this);
        });
      });
    }
  });
});
