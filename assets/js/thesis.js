$(function () {
    $('#fileupload').fileupload({
        dataType: 'json',
        done: function (e, data) {
            alert("Finished upload");
            $.each(data.result.files, function (index, file) {
                $('<p/>').text(file.name).appendTo(document.body);
            });
        }
    });
});

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
     if(!self.givenValue()) {
       self.givenNameStatus('has-error');
     } else {
       self.givenNameStatus();
     }
     
     if(!self.familyValue()) {
       self.familyNameStatus('has-error');
     } else {
       self.familyNameStatus();
     }     

     if(self.advisorList().length < 1 && !self.advisorFreeFormValue())  {
       self.advisorsStatus('has-error'); 
     } else {
       self.advisorsStatus(); 
    }

     if(!self.stepOneViewModel.isValid()) {
       return
     }  
     
     self.resetViews();
     self.showStepTwo(true);
     self.setProgressBar(20);

   }

   self.validateStepTwo = function() {
     if(!self.titleValue()) {
       self.titleValueStatus('has-error');
     } else {
       self.titleValueStatus();
     }

     if(!self.thesisFile()) {
       self.thesisFileStatus('has-error');
     } else {
       self.thesisFileStatus();
     }

     if(self.thesisKeywords.length < 1) {
       self.thesisKeywordsStatus('has-error');
     } else {
       self.thesisKeywordsStatus();
     }

     if(!self.stepTwoViewModel().isValid()) {
       return;
     }
     self.resetViews();
     self.showStepThree(true);
     self.setProgressBar(40);
   }

  self.validateStepThree = function() {
    self.resetViews();
    self.setProgressBar(60);
    self.showStepFour(true);

  }

   self.validateStepFour = function() {
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
     alert("Submitting your thesis to the Digital Archives means that your scholarly work will be shared on the open web");
     self.resetViews();
     self.setProgressBar(80);

     $("#thesis-base-form").bind('ajax:complete', function() {
         self.setProgressBar(100);
     });     

     $("#thesis-base-form").submit();


       
     
   }
 
}


function uploadFile() {
  var formData = new FormData(this);
  var fileLoadReq = new XMLHttpRequest();
  fileLoadReq.open('POST', 'uploadFile', true);
  fileLoadReq.onload = function(oEvent) {
    if(fileLoadReq.status == 200) {
      alert("File uploaded");
    } else {
      alert("Error " + fileLoadReq.status + " occurred uploading your file");
    }
  }
   fileLoadReq.send(formData);
}
