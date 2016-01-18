/**
 * Created by 东方鹗 on 15-12-16.
 */
$(function () {
    function DataBinder(object_id){
        // Use a jQuery object as simple PubSub
        var pubSub=jQuery({});

        // We expect a `data` element specifying the binding
        // in the form:data-bind-<object_id>="<property_name>"
        var data_attr="bind-"+object_id,
            message=object_id+":change";

        // Listen to chagne events on elements with data-binding attribute and proxy
        // then to the PubSub, so that the change is "broadcasted" to all connected objects
        jQuery(document).on("change","[data-]"+data_attr+"]",function(eve){
            var $input=jQuery(this);

            pubSub.trigger(message,[$input.data(data_attr),$input.val()]);
        });

        // PubSub propagates chagnes to all bound elemetns,setting value of
        // input tags or HTML content of other tags
        pubSub.on(message,function(evt,prop_name,new_val){
            jQuery("[data-"+data_attr+"="+prop_name+"]").each(function(){
                var $bound=jQuery(this);

                if($bound.is("")){
                    $bound.val(new_val);
                }else{
                    $bound.html(new_val);
                }
            });
        });
        return pubSub;
    }
    function Markdown( uid ) {
        var binder = new DataBinder( uid ),

        markdown = {
            attributes: {},

        // The attribute setter publish changes using the DataBinder PubSub
        set: function( attr_name, val ) {
            this.attributes[ attr_name ] = val;
            binder.trigger( uid + ":change", [ attr_name, val, this ] );
        },

        get: function( attr_name ) {
            return this.attributes[ attr_name ];
        },

        _binder: binder
        };

        // Subscribe to the PubSub
        binder.on( uid + ":change", function( evt, attr_name, new_val, initiator ) {
        if ( initiator !== markdown ) {
            markdown.set( attr_name, new_val );
        }
        });

        return markdown;
    }
    var md = $('.markdown').text();
    console.log('md = ' + md);
    var md_html = marked(md);
    console.log('md = ' + md_html);
    var markdown = new Markdown("md");
    markdown.set("md-html", md_html)
});