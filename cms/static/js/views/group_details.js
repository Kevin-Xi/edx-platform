define([
    'js/views/baseview'
], function(BaseView) {
    'use strict';

    var GroupDetails = BaseView.extend({
        tagName: 'div', // TODO: confirm class and tag
        className: 'group-configuration-details',

        initialize: function() {
            this.template = this.loadTemplate('group-details');
        },

        render: function() {
            this.$el.html(this.template(this.model.toJSON()));
        }
    });

    return GroupDetails;
});
