/**
 * A generic list view class.
 *
 * Expects the following properties to be overriden:
 *   - newButtonCss (string): CSS selector identifying a button which, when clicked, should add a new item to the collection and create a new item view.
 *   - emptyTemplateName (string): Name of an underscore template to render when the collection is empty.
 *   - ItemViewClass (Backbone View Class): View to render the items in the collection.
 *   - newModelOptions (object): Options to pass to models which are added to the collection.
 */
define([
    'js/views/baseview'
], function(BaseView) {
    'use strict';
    var List = BaseView.extend({
        initialize: function() {
            this.$(this.newButtonCss).click(this.addOne);
            this.emptyTemplate = this.loadTemplate(this.emptyTemplateName);
            this.listenTo(this.collection, 'add', this.addNewItemView);
            this.listenTo(this.collection, 'remove', this.handleDestory);
        },

        render: function() {
            if (this.collection.length === 0) {
                this.$el.html(this.emptyTemplate());
            } else {
                var frag = document.createDocumentFragment(),
                    ItemViewClass = this.ItemViewClass;

                this.collection.each(function(model) {
                    frag.appendChild((new ItemViewClass({model: model})).render().el);
                });

                this.$el.html([frag]);
            }

            return this;
        },

        addNewItemView: function (model) {
            var view = new this.ItemViewClass({model: model});

            // If items already exist, just append one new. Otherwise, overwrite
            // no-content message.
            if (this.collection.length > 1) {
                this.$el.append(view.render().el);
            } else {
                this.$el.html(view.render().el);
            }

            view.$el.focus();
        },

        addOne: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.collection.add({editing: true}, this.newModelOptions);
        },

        handleDestory: function () {
            if (this.collection.length === 0) {
                this.$el.html(this.emptyTemplate());
            }
        }
    });

    return List;
});
