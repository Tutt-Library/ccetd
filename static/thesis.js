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
     input.name = "keyword_" + (name_seed+i);
     span_kw.appendChild(input);
  }
 }
