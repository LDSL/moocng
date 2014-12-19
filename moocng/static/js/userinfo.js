geolocation = null;
deviceInfo = {
	type: "unknown",
	os: "unknown",
	orientation: "unknown"
};
geolocation_advised = false;
geolocation_allowed = undefined;
$(function(){
	// Check geolocation permission
	if(window.sessionStorage && window.localStorage){
		geolocation_advised = sessionStorage.getItem('geolocation_advised') == "true";
		geolocation_allowed = localStorage.getItem('geolocation_allowed');
	}

    // Device Type
    if(device.desktop()){
    	deviceInfo.type = "desktop";
    }else if(device.tablet()){
		deviceInfo.type = "tablet";
    }else if(device.mobile()){
    	deviceInfo.type = "mobile";
    }
	// Device OS
	if(deviceInfo.type != "desktop"){
		if(device.ios()){
			deviceInfo.os = "ios";
		}else if(device.android()){
			deviceInfo.os = "android";
		}else if(device.blackberry()){
			deviceInfo.os = "blackberry";
		}else if(device.windows()){
			deviceInfo.os = "windows";
		}else if(device.fxos()){
			deviceInfo.os = "firefoxos";
		}else if(device.meego()){
			deviceInfo.os = "meego";
		}
	}
	// Orientation
	if(device.landscape()){
		deviceInfo.orientation = "landscape";
	}else if(device.portrait()){
		deviceInfo.orientation = "portrait";
	}

	// Update geolocation
    if(navigator.geolocation && (geolocation_advised || geolocation_allowed == 'true')){
        navigator.geolocation.getCurrentPosition(function(position){
        		localStorage.setItem('geolocation_allowed', true);
            	geolocation = position;
        	},function(error){
        		if (error.code == error.PERMISSION_DENIED)
        			localStorage.setItem('geolocation_allowed', false);
        	},{timeout: 2000}
        );
    }else{
    	showGeolocationAdvise();
    }
});

function getBrowserName(){
    var ua= navigator.userAgent, tem, 
    M= ua.match(/(opera|chrome|safari|firefox|msie|trident(?=\/))\/?\s*(\d+)/i) || [];
    if(/trident/i.test(M[1])){
        tem=  /\brv[ :]+(\d+)/g.exec(ua) || [];
        return 'ie '+(tem[1] || '');
    }
    if(M[1]=== 'Chrome'){
        tem= ua.match(/\bOPR\/(\d+)/)
        if(tem!= null) return 'opera '+tem[1];
    }
    M= M[2]? [M[1], M[2]]: [navigator.appName, navigator.appVersion, '-?'];
    //if((tem= ua.match(/version\/(\d+)/i))!= null) M.splice(1, 1, tem[1]);
    //return M.join(' ');
    return M[0];
}

function showGeolocationAdvise(){
	console.log('Mostramos ventana');
	var browser = getBrowserName();
	var video_file = "geolocation_";
	video_file += geolocation_allowed == undefined ? 'firsttime' : 'blocked';
	video_file += '_' + browser.toLowerCase();
	video_file += '_en_640.mp4';
	var confirmDiv = $('<div id="geolocation_advise" class="modal geoadvise"> \
		<div class="modal-header"><a href="#">Entendido</a></div> \
		<div class="modal-body"> \
			<img src="/static/img/geolocation.png"> \
			<h1>¡Hola! Activa tu ubicación <span>para una mejor experiencia educativa.</span></h1> \
			<div class="video"><video autoplay loop><source src="/static/video/'+ video_file +'"></video></div> \
			<p class="label">Permiso de ubicación en '+ browser +'. <a href="#">Más información</a></p></video> \
			<p>Su navegador es '+ browser +'. Activa el posicionamiento haciendo clic en Permitir en la barra que aparecerá arriba.</p> \
		</div> \
		<div class="modal-footer"> \
			<p>¿Por qué es importante mi ubicación geográfica?</p> \
			<a href="#">Leer más</a> \
		</div></div>');
	$('body').append(confirmDiv);

    confirmModal = confirmDiv.modal({
        show: false,
        backdrop: "static",
        keyboard: false
    });
    confirmModal.modal("show");

	sessionStorage.setItem('geolocation_advised', true);
}

function sendHistoryEntry(){
	window.setTimeout(function(){
		var lat = 0.0;
		var lon = 0.0;
		var data;
		if (geolocation){
			lat = geolocation.coords.latitude;
			lon = geolocation.coords.longitude;
		}
		data = {
			lat: lat,
			lon: lon,
			timestamp: new Date().getTime(),
			url: window.location.href,
			dev_type: deviceInfo.type,
			dev_os: deviceInfo.os,
			dev_orientation: deviceInfo.orientation
		};

		$.ajax({
			url: '/api/v1/history/',
			type: 'POST',
        	contentType: "application/json",
			data: JSON.stringify(data)
		});
	},2500);
}