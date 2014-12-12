geolocation = null;
deviceInfo = {
	type: "unknown",
	os: "unknown",
	orientation: "unknown"
};
$(function(){
	// Update geolocation
    if(navigator.geolocation){
        navigator.geolocation.getCurrentPosition(function(position){
            geolocation = position;
        },null,{timeout: 2000});
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
});

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