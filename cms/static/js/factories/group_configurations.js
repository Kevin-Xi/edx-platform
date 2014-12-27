define([
    'js/collections/group_configuration', 'js/models/group_configuration', 'js/views/pages/group_configurations'
], function(GroupConfigurationCollection, GroupConfigurationModel, GroupConfigurationsPage) {
    'use strict';
    return function (experimentConfigurations, cohortConfiguration, groupConfigurationUrl, courseOutlineUrl) {
        var groupConfigurationCollection = new GroupConfigurationCollection(experimentConfigurations, {parse: true}),
            cohortGroupConfiguration = new GroupConfigurationModel(cohortConfiguration, {parse: true});

        groupConfigurationCollection.url = groupConfigurationUrl;
        cohortGroupConfiguration.urlRoot = groupConfigurationUrl;
        groupConfigurationCollection.outlineUrl = courseOutlineUrl;
        new GroupConfigurationsPage({
            el: $('#content'),
            collection: groupConfigurationCollection,
            cohortGroupConfiguration: cohortGroupConfiguration
        }).render();
    };
});
