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