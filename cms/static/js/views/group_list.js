define([
    'js/views/list', 'js/views/group_item'
], function(ListView, GroupItemView) {
    'use strict';

    var GroupList = ListView.extend({
        tagName: 'div',
        className: 'group-configurations-list',
        newButtonCss: '.new-button',
        emptyTemplateName: 'no-groups',
        ItemViewClass: GroupItemView
    });

    return GroupList;
});
