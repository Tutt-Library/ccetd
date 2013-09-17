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
   // Creator 
   self.showAuthorView = ko.observable(true);
      self.emailValue = ko.observable();
   self.familyValue  = ko.observable();
   self.givenValue  = ko.observable();
   self.gradDateValue  = ko.observable();
   self.middleValue  = ko.observable();

   // Upload Thesis
   self.showUploadThesis = ko.observable(false);
   self.pageNumberValue = ko.observable();
   self.titleValue = ko.observable();

   // Event Handlers for Thesis
   self.validateSaveCreator  = function() {
     self.showAuthorView(false);
     self.showUploadThesis(true);
   }
   
   self.validateSaveThesis = function() {
     self.showUploadThesis(false);
   }


}

