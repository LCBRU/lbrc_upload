$(function () {
	if (!Modernizr.inputtypes.date) {
	  $('input[type="date"]').datetimepicker({ format: 'YYYY-M-D'});
	}
	if (!Modernizr.inputtypes.datetime) {
	  $('input[type="datetime"]').datetimepicker({ format: 'YYYY-M-D'});
	}
});

