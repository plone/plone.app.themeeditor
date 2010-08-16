jq(function() {
  var updateResults = function() {
    jq('#plone-app-themeeditor-tags .selected').removeClass('selected');
    jq('#plone-app-themeeditor-browser').load(
      '@@plone.app.themeeditor.browse #plone-app-themeeditor-browser', 
      jq('#plone-app-themeeditor-filter-form').serialize()
    );
  }
  var activateUI = function() {
    // edit popups
    jq('a[href*=/@@plone.app.themeeditor.export]', this).prepOverlay({
      subtype: 'ajax',
      filter: '#content',
      //formselector: 'form',
          });

    jq('a[href*=/manage_main],a[href*=/@@customizezpt]', this).prepOverlay({
      subtype: 'ajax',
      filter: 'form,form+*', // everything after the 2nd table
      formselector: 'form',
      config: {
        onLoad: function() {
          // absolutize relative form actions
          var base = this.getTrigger().data('target');
          var content = document;
          if(this.getContent != undefined){
            content = this.getContent();
          }
          jq('form', content).each(function() {
            var action = jq(this).attr('action');
            if (action.charAt(0) != '/') {
              jq(this).attr('action', base.substr(0,base.lastIndexOf('/')) + '/' + action);
            }
          });
          
          // prevent customizing already-customized resources
          var source = this.getTrigger().data('source');
          if(source.find('.plone-app-themeeditor-layers.customized').size() >= 1){
              var overlay = this.getOverlay();
              overlay.find('input[type=submit]').hide();
              overlay.find('select[name=folder_path]').parent().parent().remove();
          }
        },
        onClose: function(){
          var trigger = this.getTrigger().data('source').parent();
          var title = trigger.prev('.plone-app-themeeditor-resource.open');
          trigger.load(title.attr('href'), null, function(){
            // remove custom and view info
            var dd = title.next();
            while (dd.is('dd')) {
                var to_remove = dd; dd = dd.next(); to_remove.remove();
            }
            var dd = jq(this).find('dd');
            title.after(dd);
            dd.show();
            activateUI.apply(dd);
          });
        }
      }
    });
    // removal of customized items
    jq('a[href*=/manage_delObjects]', this).click(function(e) {
      e.preventDefault();
      jq.get(jq(this).attr('href'));
      jq(this).closest('dd').remove();
    });
  }
  activateUI.apply(jq('#plone-app-themeeditor-export'));
  activateUI.apply(jq('#plone-app-themeeditor-browser'));
  // update results via AJAX
  jq('#plone-app-themeeditor-filter-form').submit(function(e) {
    e.preventDefault();
    updateResults();
  });
  // collapsible layer lists
  jq('.plone-app-themeeditor-resource').live('click', function(e) {
    e.preventDefault();
    var link = jq(this);
    link.toggleClass('open');
    var dd = jq(this).next();
    if (dd.is('dd')) {
      while(dd.is('dd')) { dd.slideToggle('fast'); dd = dd.next(); }
    } else {
      jq('<div><' + '/div>').load(jq(this).attr('href'), null, function() {
        jq('dd', this).insertAfter(link).slideDown('fast').each(function() {
          activateUI.apply(this);
        });
      });
    }
  });
});
