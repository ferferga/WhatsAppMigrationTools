# Sample databases

Here are some original WhatsApp databases (previously emptied for removing personal information) for reference, they will be really useful if you're debugging a problem or trying to improve my scripts (I wish I had them as accesible like this when I first started in this project).

Although WhatsApp have more databases that the ones mentioned here, these are the ones where we will be doing all the work for moving the messages from one platform to the other.

## Windows Phone databases

* **calls.db**: This database stores all the information about calls and videocalls. Information such as call logs, the result of the call (if it was answered, missed or declined), etc... Are stored here. Extracted from my own WhatsApp install around December-January 2018/2019.

* **messages.db**: This is the main and most important database in the WP's version of WhatsApp. It stores messages, the thumbnails of the images, some info about your contacts, etc...
Extracted from my own WhatsApp install around December-January 2018/2019.

## Android databases

* **msgstore_old.db**: The equivalent of ``messages.db``, but in Android. This exact one was extracted from a WhatsApp version released between November 2018 and January 2019. 

*WPWhatsAppToAndroid script will generate a database with this schema*

* **msgstore.db**: Same as *msgstore_old.db*, but with a more recent schema. This one in particular was extracted from ``2.19.360`` (January 2020)

*Merger script will generate a database with this schema*