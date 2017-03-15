ko.validation.rules['pdfOnly'] = {
    validator: function (val, validate) {
        return val.match(/\\([^\\]+).pdf$/);
    },
    message: 'Must be empty or an integer value'
};



//ko.validation.rules['pdfOnly'] = {
//   validator: function (element, bool) {
//        function isPDF(str) {
//         return str.split(".")[0] === 'pdf'; 
//        }
   
//        return isPDF(element);
//    },
//     message: "Thesis MUST be a PDF"
//};
ko.validation.registerExtenders();


// Thesis Javascript file
function AddKeywords()
 {
  var span_kw = document.getElementById('span-keywords');
  var name_seed = span_kw.childNodes.length - 1;
  if (name_seed > 7)
  {
    var more_anchor = document.getElementById('more-a');
    more_anchor.style.visibility = "hidden";
  } 
  span_kw.appendChild(document.createElement('br'));

  for(i=0;i<=2;i++)
  {

     var input = document.createElement('input');
     input.type = 'text';
     input.size = 20;
     input.name = "subject-keyword_" + (name_seed+i);
     span_kw.appendChild(input);
  }
 }

// Thesis Knockout.js View Models
function ThesisViewModel() {
   var self = this;
   self.formError = ko.observable(false);
   self.formErrors = ko.observableArray();
   self.thesisProgressValue = ko.observable(0);
   self.thesisProgressWidth = ko.observable('width: 0%');
   self.thesisPID = ko.observable("");

   // Creator 
   // Step One
   self.showStepOne = ko.observable(true);
   self.advisorList = ko.observableArray();
   self.advisorFreeFormValue = ko.observable();
   self.advisorsStatus = ko.observable();
   self.emailValue = ko.observable();
   self.familyValue  = ko.observable().extend({ required: true });
   self.familyNameStatus = ko.observable();
   self.givenValue  = ko.observable().extend({ required: true });
   self.givenNameStatus = ko.observable();
   self.gradDateValue  = ko.observable();
   self.middleValue = ko.observable();
   self.suffixValue = ko.observable();

   self.stepOneViewModel = ko.validatedObservable({
       given: self.givenValue,
       family: self.familyValue
   });

   // Step Two
   self.showStepTwo = ko.observable(false);
   self.thesisFileStatus = ko.observable();
   self.thesisKeywordsStatus = ko.observable();
   self.titleValueStatus = ko.observable();
   self.hasIllustrations = ko.observable();
   self.hasMaps = ko.observable();
   self.pageNumberValue = ko.observable();
   self.thesisAbstract = ko.observable();
   // PDF only custom validation rule
   self.thesisFile = ko.observable().extend({ required: true });
      
   self.titleValue = ko.observable().extend({ required: true });
   self.thesisKeywords = ko.observableArray([
     { name: 'keyword1' },
     { name: 'keyword2' },
     { name: 'keyword3' }
   ]).extend({ minLength: 1 });

   self.stepTwoViewModel = ko.validatedObservable({
     keyword: self.thesisKeywords,
     thesisFile: self.thesisFile,
     title: self.titleValue
   });

   // Thesis Support Files
   // Step Three
   self.showStepThree = ko.observable(false);

   // Thesis Honor Code
   // Step Four
   self.showStepFour = ko.observable(false);
   self.honorCodeError = ko.observable(false);
   self.hasHonorCode = ko.observable().extend({ required: true });
   self.hasSubmissionAgreement = ko.observable().extend({ required: true });
   self.submissionAgreementError = ko.observable(false);

   self.stepFourViewModel = ko.validatedObservable({
     honorCode: self.hasHonorCode,
     submissionAgreement: self.hasSubmissionAgreement
   });

   // Event Handlers for Thesis
   self.backStepOne = function() {
     self.resetViews();
     self.showStepOne(true);

   }
   self.backStepTwo = function() {
     self.resetViews();
     self.showStepTwo(true);
   }

   self.backStepThree = function() {
     self.resetViews();
     self.showStepThree(true);
   }
 
   self.enableContinueHonorBtn = function() {
     if(self.hasHonorCode() == true && self.hasSubmissionAgreement()) {
        self.ContinueHonorCodeBtn(true);
     }
   }

   self.resetViews = function() {
     self.showStepOne(false);
     self.showStepTwo(false);
     self.showStepThree(false);
     self.showStepFour(false);
   }

   self.addKeyword = function() {
     var last_field = $('#keywords > li').prev();
     last_field.last().after("<li><input name='keyword' type='text' class='form-control' maxlength='255'></input></li>");

   }

   self.setProgressBar = function(value) {
     self.thesisProgressValue(value);
     self.thesisProgressWidth('width: ' + value + '%');
   }


   self.validateStepOne = function()  {
     self.formError(false);
     self.formErrors.removeAll();
     if(!self.givenValue()) {
       self.givenNameStatus('has-error');
       self.formErrors.push({'error': 'First name is required'});
     } else {
       self.givenNameStatus();
     }
     
     if(!self.familyValue()) {
       self.familyNameStatus('has-error');
       self.formErrors.push({'error': 'Last name is required'});

     } else {
       self.familyNameStatus();
     }     

     if(self.advisorList().length < 1 && !self.advisorFreeFormValue())  {
       self.advisorsStatus('has-error'); 
       self.formErrors.push({'error': 'At least one advisor is required'});
     } else {
       self.advisorsStatus(); 
    }

     if(!self.stepOneViewModel.isValid()) {
       self.formError(true);
       return
     }  
     
     self.resetViews();
     self.showStepTwo(true);
     self.setProgressBar(20);

   }

   self.validateStepTwo = function() {
     self.formError(false);
     self.formErrors.removeAll();

     if(!self.titleValue()) {
       self.titleValueStatus('has-error');
       self.formErrors.push({'error': 'Title is required'});
     } else {
       self.titleValueStatus();
     }

     if(!self.thesisFile()) {
       self.thesisFileStatus('has-error');
       self.formErrors.push({'error': 'Thesis File is required'});
     } else {
       var filename = $('#thesis_file').val().replace(/.*(\/|\\)/, '');
       var file_parts = filename.split(".");
       var ext = '';
       if (file_parts.length > 1) {
          ext = file_parts[1];  
       }
       ext = ext.toLowerCase();
       if(ext != 'pdf' && ext != 'mp4') {
         self.thesisFileStatus('has-error');
         self.formErrors.push({'error': 'File must be a PDF/A or MP4'});
       } else {
         self.thesisFileStatus();
       }
     }
    var emptyKeywords = true;
    $("input[name$='keyword']").each(
     function(index) { 
        if($(this).val().length > 0) { 
          emptyKeywords=false; 
        } 
      });
    if(emptyKeywords == true) {
       self.thesisKeywordsStatus('has-error');
       self.formErrors.push({'error': 'At least one keyword is required'});
     } else {
       self.thesisKeywordsStatus('');
     }

     if(!self.stepTwoViewModel().isValid() || self.formErrors().length > 0) {
       self.formError(true);
       return;
     } 
     self.resetViews();
     self.showStepThree(true);
     self.setProgressBar(40);
   }

  self.validateStepThree = function() {
    self.formError(false);
    self.formErrors.removeAll();
    self.resetViews();
    self.setProgressBar(60);
    self.showStepFour(true);

  }

  self.validateStepFour = function() {
    self.formError(false);
    self.formErrors.removeAll();

     if(!self.hasHonorCode()) {
      self.honorCodeError(true);
     } else {
       self.honorCodeError(false);
     }
     if(!self.hasSubmissionAgreement()) {
       self.submissionAgreementError(true);
     } else {
       self.submissionAgreementError(true);
     }
     if(!self.stepFourViewModel().isValid()) {
       return;
     }

     self.resetViews();
     self.setProgressBar(80);
     $("#thesis-base-form").submit();


       
     
   }
 
}

