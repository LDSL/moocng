function showHelpForm(){
	var helpDiv = '<div id="helpForm" class="modal geoadvise"> \
		<div class="modal-body fixedHeight"> \
			<img src="/static/img/ECO_icon_ayudame_black.svg"> \
			<h1>'+ helpForm_translate.greeting +' <span>'+ helpForm_translate.greeting_2 +'.</span></h1> \
			<form> \
				<input type="text" id="help_subject" placeholder="' + helpForm_translate.subject + '" required> \
				<textarea id="help_body" placeholder="' + helpForm_translate.body + '" required></textarea> \
				<input type="button" class="button close" value="'+ helpForm_translate.cancel_button +'"> \
				<input type="submit" class="button squared" value="'+ helpForm_translate.send_button +'"> \
			</form> \
		</div> \
		<div class="modal-footer"> \
			<p>### DISCLAIMER O INFO ###</p> \
		</div> \
		</div>';
		
	var $helpDiv = $(helpDiv);
	$('body').append($helpDiv);

    helpModal = $helpDiv.modal({
        show: false,
        backdrop: "static",
        keyboard: false
    });
    setTimeout(function(){ helpModal.modal("show"); }, 100);    

    $helpDiv.find('input.close').click(function(){
    	helpModal.modal("hide");
    	setTimeout(function(){ helpModal.remove(); }, 1000);
    });

    $helpDiv.find('form').submit(function(e){
    	e.preventDefault();

        var submitBtn = $('#helpForm input[type=submit]');
        submitBtn.val(helpForm_translate.sending).attr('disabled',true);

    	var $target = $(e.target);
    	var subject = $target.find('#help_subject').val();
    	var body = $target.find('#help_body').val();
        var lat = 0.0, lon = 0.0;
        if(geolocation){
            lat = geolocation.coords.latitude;
            lon = geolocation.coords.longitude;
        }
        var url = window.location.href;
        var device = deviceInfo.type;
        var orientation = deviceInfo.orientation;
        var os = deviceInfo.os;
        var browser = getBrowserName()
    	$.ajax({
    		url: '/contact/support',
    		type: 'POST',
    		data: {
    			'subject': subject,
    			'body': body,
                'url': url,
                'lat': lat,
                'lon': lon,
                'device': device,
                'orientation': orientation,
                'os': os,
                'browser': browser,
    		},
    		success: function(response){
    			helpModal.modal("hide");
    			setTimeout(function(){ helpModal.remove(); }, 1000);
                submitBtn.val(helpForm_translate.send_button).removeAttr('disabled');
    		},
            error: function(response){
                alert(helpForm_translate.error);
                submitBtn.val(helpForm_translate.send_button).removeAttr('disabled');
            }

    	});
    });
}

$('#help_button').click(function(e){
	e.preventDefault();
	showHelpForm();
});
