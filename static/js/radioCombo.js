//this file sets up a radio combo - the user selects radio buttons, and each radio button
//that the user clicks enables a corresponding input field and disables all other input fields in the combo

$(document).ready(function() {
	
	//set up radio combo
	$('.radioCombo').each(function(i,e) {
		setupRadioCombo($(e));
	});
});

var setupRadioCombo = function(element) {
	
	//set up the change event handler for each radio button
	element.on('change','.radioComboEntry input[type="radio"]', function(ev) {
		
		//disable all input fields in this radio combo
		$(ev.currentTarget).closest('.radioCombo').find('.radioComboEntry .text input').prop('disabled',true);
		
		//enable this radio button's input fields
		$(ev.currentTarget).closest('.radioComboEntry').find('.text input').prop('disabled',false);
	});
	
	//if anything is already selected, make sure everything else is disabled
	element.find('.radioComboEntry input:checked').trigger('change');
}