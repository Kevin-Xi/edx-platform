define([
    'js/views/list', 'js/views/group_configuration_item'
], function(ListView, GroupConfigurationItemView) {
    'use strict';

    var GroupConfigurationsList = ListView.extend({
        tagName: 'div',
        className: 'group-configurations-list',
        newButtonCss: '.new-button',
        newModelOptions: {addDefaultGroups: true},
        emptyTemplateName: 'no-group-configurations',
        ItemViewClass: GroupConfigurationItemView
    });

    return GroupConfigurationsList;
});
