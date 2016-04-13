var bookkeepr = {
    flash: function (message, kind) {
        document.getElementById("alert-container").className="alert alert-" + kind;
        document.getElementById("alert-container").innerHTML="<p>" + message + "</p>";
        $("#alert-container").slideDown();
        setTimeout(function() {
            $("#alert-container").slideUp();
        }, 2500);
    },

    followUser: function(id) {
        //var title = document.getElementById("listname").value;
        $.post("/follow", {
            id: id
        }).done(function(code) {
            $("#followUserButton").html("Followed!");
            $("#followUserButton").attr("disabled", "disabled");
        });
    }, 

    unfollowUser: function(id) {
        //var title = document.getElementById("listname").value;
        $.post("/unfollow", {
            id: id
        }).done(function(code) {
            $("#unfollowUserButton").html("Unfollowed!");
            $("#unfollowUserButton").attr("disabled", "disabled");
        });
    },

    deleteKey: function(key) {
        $.post("/delete/key", {
            key: key
        }).done(function(code) {

        });
    }

};