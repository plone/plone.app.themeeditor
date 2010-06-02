jq(function() {
  var updateResults = function() {
    jq('#plone-app-skineditor-tags .selected').removeClass('selected');
    jq('#plone-app-skineditor-browser').load(
      '@@plone.app.skineditor.browse #plone-app-skineditor-browser', 
      jq('#plone-app-skineditor-filter-form').serialize()
    );
  }
  var activateUI = function() {
    // edit popups
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
          
          var source = this.getTrigger().data('source');
          if(source.find('h3 span.plone-app-skineditor-active').size() != 1){
              var overlay = this.getOverlay();
              overlay.find('input[type=submit]').hide();
              overlay.find('select[name=folder_path]').parent().parent().remove();
          }
        },
        onClose: function(){
          var trigger = this.getTrigger().data('source').parent();
          var title = trigger.prev('.plone-app-skineditor-resource.open');
          trigger.load(title.attr('href'), null, function(){
            title.nextUntil('.plone-app-skineditor-resource').remove(); //remove custom and view info
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
  activateUI.apply(jq('#plone-app-skineditor-browser'));
  // update results via AJAX
  jq('#plone-app-skineditor-filter-form').submit(function(e) {
    e.preventDefault();
    updateResults();
  });
  // collapsible layer lists
  jq('.plone-app-skineditor-resource').live('click', function(e) {
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