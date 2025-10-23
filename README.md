# Data Management System
This repo is for the Data Management System (DMS). It is a sub component for my honours project looking into the automation of AI training, Specifically training of detection models for trees. The DMS is responsible for storing and handling all metadata todo with image, annotations, datasets, and models


## Pre Requisites 

This system is designed to be used in conjunction with MongoDB, it can be used on any platform except for line 172 in dataset_handler.py which uses a linux command. Therefore to use on windows that line needs to be converted/changed

## IPS Interaction 
While designed to interact with the IPS over the network, in practise some methods expect the IPS and DMS to be running on the same machine. As they copy files rather then sending over network. This will need to change to enable distributed deployment. 
