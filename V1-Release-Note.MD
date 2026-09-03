Python SDK for Egyptian Tax Authority (ETA) eInvoicing integration.

design Pattern
Factory Method: Defines an interface for creating an object but lets subclasses decide which specific class to instantiate 


Model Pattern :
 	BaseModel 

Phase 1 
Submit Documents 
refrence link :
https://sdk.invoicing.eta.gov.eg/einvoicingapi/01-submit-documents/  

After finish phase one create usage documentation 

Phase 2 
Invoicing 
Create module for each invoice type 
Allow user to set the moduel data 
refrence link :
https://sdk.invoicing.eta.gov.eg/types/#invoice

in this phase allow user to generate json for each invoice type 
to be able to send to Submit document api
After finish phase 2 create usage documentation 


phase 3 
Generate Signuture 
refrence link :
https://sdk.invoicing.eta.gov.eg/documents/invoice-v1-0/#signature 
Refrence repo in C# 
https://github.com/bassemAgmi/EInvoicingSigner  
allow user to send jsno file and get the signuture in valid format 
After finish phase 3  create usage documentation 

phase 4 
Cancel Document 
refrence link :
https://sdk.invoicing.eta.gov.eg/einvoicingapi/02-cancel-document/
After finish phase 4  create usage documentation 

phase 5 
Reject Document
refrence link :
https://sdk.invoicing.eta.gov.eg/einvoicingapi/03-reject-document/
After finish phase 5  create usage documentation 

phase 6 
Get Recent Documents
refrence link :
https://sdk.invoicing.eta.gov.eg/einvoicingapi/04-get-recent-documents/
After finish phase 6  create usage documentation 


phase 7 
Search Documents 
refrence link :
https://sdk.invoicing.eta.gov.eg/einvoicingapi/16-search-documents/ 
After finish phase 7  create usage documentation 


phase 8 
Request Document Package
refrence link :
https://sdk.invoicing.eta.gov.eg/einvoicingapi/05-request-document-package/
After finish phase 8  create usage documentation 

phase 9 
Get Package Requests 
refrence link :
https://sdk.invoicing.eta.gov.eg/einvoicingapi/06-get-package-requests/
After finish phase 9  create usage documentation 