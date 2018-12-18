# Templates for Azure VMs

<a href="https://portal.azure.com/#create/Microsoft.Template/uri/https://raw.githubusercontent.com/jeferrb/AzureTemplates/master/azuredeploy.json" target="_blank">
    <img src="http://azuredeploy.net/deploybutton.png"/>
</a>
<a href="http://armviz.io/#/?load=https://raw.githubusercontent.com/jeferrb/AzureTemplates/master/azuredeploy.json" target="_blank">
    <img src="http://armviz.io/visualizebutton.png"/>
</a>

Template that contemplates VMs:
* with or without GPUs
* with Singularity installed

The default configuration is:
VM size:
* Standard_A8

Storage:
* Standard_LRS

It is possible to change the configurations by using the following parameters:
* vmSize -> type of VM instance
* storageAccountType -> type of storage account
* ImageOffer -> Linux distro
* OSVersion -> Distro version
* ImagePublisher -> Publisher of the image in use
*
Supported VM sizes:
* Standard&#95;D2s&#95;v3 (No GPU)
* Standard&#95;NC6 (GPU enabled)

(The availability changes depending on the region selected for the deployment - Default West US 2 includes all supported sizes)

Commands:
Creating Resource Group:
* az group create --name &lt;ResourceGroupName&gt; --location "West US 2"

Deploying Ubuntu:
* az group deployment create \
    --name &lt;VMname&gt; \
    --resource-group &lt;ResourceGroupName&gt; \
    --template-uri "https://raw.githubusercontent.com/jeferrb/AzureTemplates/master/azuredeploy.json"
    --parameters ImageOffer=UbuntuServer ImagePublisher=Canonical OSVersion=16.04

Deploying CentOS:
* az group deployment create \
    --name &lt;VMname&gt; \
    --resource-group &lt;ResourceGroupName&gt; \
    --template-uri "https://raw.githubusercontent.com/jeferrb/AzureTemplates/master/azuredeploy.json"
    --parameters ImageOffer=CentOS-HPC ImagePublisher=OpenLogic OSVersion=7.3
