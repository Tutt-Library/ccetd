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

   // Creator 
   self.showAuthorView = ko.observable(true);
   self.advisorList = ko.observableArray();
   self.advisorFreeFormValue = ko.observable();
   self.advisorsStatus = ko.observable();
   self.emailValue = ko.observable();
   self.familyValue  = ko.observable();
   self.familyNameStatus = ko.observable();
   self.givenValue  = ko.observable();
   self.givenNameStatus = ko.observable();
   self.gradDateValue  = ko.observable();
   self.middleValue = ko.observable();
   self.suffixValue = ko.observable();

   // Upload Thesis
   self.showUploadThesis = ko.observable(false);
   self.pageNumberValue = ko.observable();
   self.titleValue = ko.observable();

   // Thesis Support Files
   self.showThesisSupport = ko.observable(false);

   // Thesis Honor Code
   self.showHonorCode = ko.observable(false);
   self.hasHonorCode = ko.observable();
   self.hasSubmissionAgreement = ko.observable();
   self.ContinueHonorCodeBtn = ko.observable(false);

   // Thesis Review and Submit
   self.showReviewSubmit = ko.observable(false);

   // Event Handlers for Thesis
   self.enableContinueHonorBtn = function() {
     if(self.hasHonorCode() == true && self.hasSubmissionAgreement()) {
        self.ContinueHonorCodeBtn(true);
     }
   }

   self.resetViews = function() {
     self.showAuthorView(false);
     self.showUploadThesis(false);
     self.showThesisSupport(false);
     self.showHonorCode(false);
     self.showReviewSubmit(false);
   }

   self.setProgressBar = function(value) {
     self.thesisProgressValue(value);
     self.thesisProgressWidth('width: ' + value + '%');
   }

   self.submitThesis = function() {
     self.resetViews();
     self.setProgressBar(100);
   }

   self.validateSaveCreator = function()  {
     if(!self.givenValue()) {
       self.givenNameStatus('has-error');
       self.formError(true);
     }
     
     if(!self.familyValue()) {
       self.familyNameStatus('has-error');
       self.formError(true);
     }
     if(self.advisorList().length < 1 && !self.advisorFreeFormValue())  {
       self.advisorsStatus('has-error'); 
       self.formError(true);
     }
     if(self.formError()) {
       return;
     }
     var csrf_token = document.getElementsByName('csrfmiddlewaretoken')[0].value;
     var data = {
       csrfmiddlewaretoken: csrf_token,
       family: self.familyValue(),
       given: self.givenValue(),
       middle: self.middleValue(),
       suffix: self.suffixValue()
     }
     $.ajax({
       data: data,
       dataType: 'json',
       type: 'POST', 
       url: 'update',
       success: function(response) {
         self.resetViews();
         self.showUploadThesis(true);
         self.setProgressBar(20);
        }
       });
 
   }
 
   self.validateHonorCode = function() {
     self.resetViews();
     self.showReviewSubmit(true);
     self.setProgressBar(80);
   }
 
   self.validateSaveThesis = function() {
     self.resetViews();
     self.showThesisSupport(true);
     self.setProgressBar(40);
   }

   self.validateThesisSupport = function() {
     self.resetViews();
     self.showHonorCode(true);
     self.setProgressBar(60);
   }
}

